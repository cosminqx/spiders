"""
Spider: website_audit
Target: URLs discovered by pagini_aurii spider (or any CSV of URLs)
Purpose: Deep-audit each business's website to compute a quality score.
         Staleness, mobile-friendliness, SSL, CMS detection, analytics presence.
         This is what lets Tudor say: "Your site hasn't been updated since 2019
         and 60% of your visitors are on mobile — you're losing them."

Run locally:
    scrapy crawl website_audit -a input_file=output/pagini_aurii/latest.csv

Zyte Cloud schedule: triggered after pagini_aurii run completes
"""
import re
import csv
import os
import scrapy
from datetime import datetime, timezone
from urllib.parse import urlparse

from seek_intelligence.items import WebsiteAuditItem


# ── CMS / Platform fingerprints ──────────────────────────────────────────────
CMS_FINGERPRINTS = {
    "WordPress":    ["/wp-content/", "/wp-includes/", "wp-json", "wordpress"],
    "Wix":          ["wix.com", "wixstatic.com", "_wix_"],
    "Squarespace":  ["squarespace.com", "squarespace-cdn", "sqsp"],
    "Shopify":      ["cdn.shopify.com", "myshopify.com", "shopify.com/s/"],
    "Webflow":      ["webflow.com", "webflow.io"],
    "PrestaShop":   ["prestashop", "presta-shop"],
    "OpenCart":     ["opencart", "catalog/view/theme"],
    "Joomla":       ["joomla", "/components/com_"],
    "Weebly":       ["weebly.com", "weeblysite.com"],
    "Custom":       [],   # fallback
}

ANALYTICS_PATTERNS = {
    "Google Analytics": ["gtag", "google-analytics.com", "UA-", "G-"],
    "Facebook Pixel":   ["fbq(", "facebook.com/tr", "connect.facebook.net"],
    "Hotjar":           ["hotjar.com", "hj("],
    "HubSpot":          ["hs-scripts.com", "hubspot.com"],
}


class WebsiteAuditSpider(scrapy.Spider):
    name = "website_audit"

    custom_settings = {
        "ZYTE_API_DEFAULT_PARAMS": {
            # Use HTTP API (not browser) for speed — we just need headers + HTML
            "httpResponseBody": True,
            "httpResponseHeaders": True,
            "geolocation": "RO",
        },
        "DOWNLOAD_DELAY": 1.5,
        "CONCURRENT_REQUESTS": 8,   # audits are fast — parallelise more
        "DEPTH_LIMIT": 1,
    }

    def __init__(self, input_file=None, urls=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.input_file = input_file
        self.extra_urls = [u.strip() for u in urls.split(",")] if urls else []

    def start_requests(self):
        urls_to_audit = list(self.extra_urls)

        # Load URLs from CSV output of pagini_aurii / facebook_ads
        if self.input_file and os.path.exists(self.input_file):
            with open(self.input_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    url = row.get("website_url") or row.get("landing_url") or ""
                    if url and url.startswith("http"):
                        urls_to_audit.append(url)

        if not urls_to_audit:
            # Fallback: look for latest CSV from pagini_aurii run
            latest = self._find_latest_csv("output/pagini_aurii")
            if latest:
                self.logger.info(f"[website_audit] Auto-loading {latest}")
                with open(latest, encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        url = row.get("website_url", "")
                        if url and url.startswith("http"):
                            urls_to_audit.append(url)

        # Deduplicate
        seen    = set()
        for url in urls_to_audit:
            norm = self._normalize_url(url)
            if norm not in seen:
                seen.add(norm)
                yield scrapy.Request(
                    norm,
                    callback=self.parse_website,
                    meta={
                        "zyte_api": {
                            "httpResponseBody":    True,
                            "httpResponseHeaders": True,
                        },
                    },
                    errback=self.handle_error,
                )

    # ── Website audit ─────────────────────────────────────────────────────────

    def parse_website(self, response):
        html  = response.text
        url   = response.url

        item = WebsiteAuditItem()
        item["url"]          = url
        item["http_status"]  = response.status
        item["load_ok"]      = response.status == 200
        item["source"]       = self.name
        item["scraped_at"]   = datetime.now(timezone.utc).isoformat()

        # SSL
        item["has_ssl"] = url.startswith("https://")

        # Mobile-friendly (viewport meta)
        item["has_viewport_meta"] = bool(
            response.css("meta[name='viewport']").get()
        )

        # Page title & meta description
        item["page_title"]       = self._clean(response.css("title::text").get())
        item["meta_description"] = self._clean(
            response.css("meta[name='description']::attr(content)").get()
        )

        # Copyright year — staleness signal
        copyright_year = self._extract_copyright_year(response)
        item["copyright_year"]  = copyright_year
        item["staleness_signal"] = self._staleness(copyright_year)

        # Last-Modified header
        item["last_modified"] = response.headers.get("Last-Modified", b"").decode("utf-8", errors="ignore")

        # CMS detection
        item["cms_detected"] = self._detect_cms(html, response)

        # Analytics presence
        analytics = self._detect_analytics(html)
        item["has_analytics"] = bool(analytics)

        # Contact form detection
        item["has_contact_form"] = bool(
            response.css("form[id*='contact'], form[class*='contact'], input[name='email']").get()
        )

        # Audit score (0–10)
        item["audit_score"] = self._compute_audit_score(item)

        yield item

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _extract_copyright_year(self, response):
        """Find copyright year in footer — best staleness proxy."""
        footer_text = " ".join(response.css("footer ::text, [class*='footer'] ::text").getall())
        m = re.search(r"©\s*(\d{4})|copyright\s*[©]?\s*(\d{4})", footer_text, re.IGNORECASE)
        if m:
            return int(m.group(1) or m.group(2))
        # Fallback: any 4-digit year in 2000-2029 range in footer
        years = re.findall(r"\b(20[012]\d)\b", footer_text)
        if years:
            return int(max(years))
        return None

    @staticmethod
    def _staleness(year):
        if not year:
            return "unknown"
        current = datetime.now().year
        if year >= current - 1:
            return "recent"
        if year >= current - 4:
            return "ageing"
        return "outdated"   # 5+ years old = strong sales signal

    @staticmethod
    def _detect_cms(html, response):
        for cms, fingerprints in CMS_FINGERPRINTS.items():
            if any(fp.lower() in html.lower() for fp in fingerprints):
                return cms
        return "unknown"

    @staticmethod
    def _detect_analytics(html):
        found = []
        for tool, patterns in ANALYTICS_PATTERNS.items():
            if any(p in html for p in patterns):
                found.append(tool)
        return found

    @staticmethod
    def _compute_audit_score(item):
        """0–10 website quality score (LOWER = worse website = better lead for us)."""
        score = 10
        if not item.get("has_ssl"):            score -= 2
        if not item.get("has_viewport_meta"):  score -= 2
        if item.get("staleness_signal") == "outdated": score -= 3
        if item.get("staleness_signal") == "ageing":   score -= 1
        if not item.get("has_analytics"):      score -= 1
        if not item.get("has_contact_form"):   score -= 1
        return max(0, score)

    @staticmethod
    def _normalize_url(url):
        if not url.startswith("http"):
            url = "https://" + url
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

    @staticmethod
    def _find_latest_csv(directory):
        if not os.path.exists(directory):
            return None
        csvs = [os.path.join(directory, f) for f in os.listdir(directory) if f.endswith(".csv")]
        return max(csvs, key=os.path.getmtime) if csvs else None

    @staticmethod
    def _clean(text):
        if not text:
            return None
        return re.sub(r"\s+", " ", text).strip() or None

    def handle_error(self, failure):
        self.logger.warning(f"[website_audit] Failed: {failure.request.url} — {failure.value}")
