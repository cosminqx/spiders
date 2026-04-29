"""
Spider: facebook_ads
Target: https://www.facebook.com/ads/library/
Purpose: Find Romanian businesses that are actively running paid ads.
         Businesses spending on ads + weak website = hottest leads for Seek Digital.

The Ad Library is fully public — no login required.
We use Zyte's browserHtml mode to render the React app and extract ad data.

Run locally:
    scrapy crawl facebook_ads -a query=restaurant -a country=RO -o ads.csv

Zyte Cloud schedule: every 3 days
"""
import re
import json
import scrapy
from datetime import datetime, timezone, date
from urllib.parse import urlencode, quote_plus

from seek_intelligence.items import FacebookAdItem


# ── Industry search terms for Romanian market ──────────────────────────────────
INDUSTRY_QUERIES = {
    "horeca":    ["restaurant", "cafenea", "bar", "pizza", "meniu", "rezervare masa"],
    "beauty":    ["salon", "coafor", "unghii", "make-up", "infrumusetare"],
    "medical":   ["clinica", "stomatolog", "dentist", "cabinet medical", "consultatii"],
    "auto":      ["service auto", "vulcanizare", "tinichigerie", "detailing"],
    "fitness":   ["sala fitness", "gym", "antrenament", "nutritie sportiva"],
    "retail":    ["magazin", "produse", "livrare", "comanda online"],
    "real_estate": ["agentie imobiliara", "apartament vanzare", "casa vanzare"],
}

FB_AD_LIBRARY_BASE = "https://www.facebook.com/ads/library/"


class FacebookAdsSpider(scrapy.Spider):
    name = "facebook_ads"
    allowed_domains = ["facebook.com"]

    custom_settings = {
        "ZYTE_API_DEFAULT_PARAMS": {
            "browserHtml": True,
            "javascript":  True,
            "geolocation": "RO",
            "device":      "desktop",
            # Wait for the React app to hydrate
            "actions": [
                {"action": "waitForSelector", "selector": {"type": "css", "value": "[data-testid='ad-library-result']"}, "timeout": 10000},
            ],
        },
        "DOWNLOAD_DELAY": 4,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    def __init__(self, query=None, industry=None, country="RO", max_pages=5, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.country   = country
        self.max_pages = int(max_pages)

        if query:
            self.queries = [{"term": q.strip(), "industry": "custom"} for q in query.split(",")]
        elif industry and industry in INDUSTRY_QUERIES:
            self.queries = [{"term": t, "industry": industry} for t in INDUSTRY_QUERIES[industry]]
        else:
            # Default: run all industries
            self.queries = [
                {"term": term, "industry": industry}
                for industry, terms in INDUSTRY_QUERIES.items()
                for term in terms
            ]

    def start_requests(self):
        for q in self.queries:
            params = {
                "active_status":  "active",
                "ad_type":        "all",
                "country":        self.country,
                "q":              q["term"],
                "search_type":    "keyword_unordered",
                "media_type":     "all",
            }
            url = f"{FB_AD_LIBRARY_BASE}?{urlencode(params)}"
            yield scrapy.Request(
                url,
                callback=self.parse_results,
                meta={
                    "query":    q["term"],
                    "industry": q["industry"],
                    "page":     1,
                    "zyte_api": {
                        "browserHtml": True,
                        "javascript":  True,
                        "geolocation": "RO",
                        "actions": [
                            {"action": "waitForTimeout", "timeout": 3000},
                        ],
                    },
                },
                errback=self.handle_error,
            )

    # ── Results page ──────────────────────────────────────────────────────────

    def parse_results(self, response):
        query    = response.meta["query"]
        industry = response.meta["industry"]

        # FB Ad Library injects data into a __SERVER_DATA__ or similar script tag
        # We try JSON extraction first, fall back to HTML selectors
        items_from_json = list(self._extract_from_json(response, query, industry))
        if items_from_json:
            yield from items_from_json
        else:
            yield from self._extract_from_html(response, query, industry)

        # Load more / pagination via scroll-triggered endpoint
        if response.meta["page"] < self.max_pages:
            cursor = response.css("[data-cursor]::attr(data-cursor)").get()
            if cursor:
                params = {
                    "active_status": "active",
                    "ad_type":       "all",
                    "country":       self.country,
                    "q":             query,
                    "after":         cursor,
                }
                url = f"{FB_AD_LIBRARY_BASE}?{urlencode(params)}"
                yield scrapy.Request(
                    url,
                    callback=self.parse_results,
                    meta={
                        "query":    query,
                        "industry": industry,
                        "page":     response.meta["page"] + 1,
                        "zyte_api": {"browserHtml": True, "javascript": True, "geolocation": "RO"},
                    },
                    errback=self.handle_error,
                )

    def _extract_from_json(self, response, query, industry):
        """
        FB sometimes embeds ad data in script tags as JSON.
        We try to extract it before falling back to CSS selectors.
        """
        scripts = response.css("script[type='application/json']::text, script::text").getall()
        for script in scripts:
            if '"ad_archive_id"' not in script and '"page_name"' not in script:
                continue
            try:
                data = json.loads(script)
                ads  = self._walk_json_for_ads(data)
                for ad in ads:
                    item = self._build_item_from_json(ad, query, industry)
                    if item:
                        yield item
                return  # found structured data, stop searching scripts
            except (json.JSONDecodeError, TypeError):
                continue

    def _walk_json_for_ads(self, data, depth=0):
        """Recursively walk JSON to find ad objects."""
        if depth > 8:
            return
        if isinstance(data, dict):
            if "ad_archive_id" in data or "page_name" in data:
                yield data
            else:
                for v in data.values():
                    yield from self._walk_json_for_ads(v, depth + 1)
        elif isinstance(data, list):
            for item in data:
                yield from self._walk_json_for_ads(item, depth + 1)

    def _build_item_from_json(self, ad, query, industry):
        start_str = ad.get("start_date") or ad.get("ad_delivery_start_time", "")
        stop_str  = ad.get("end_date")   or ad.get("ad_delivery_stop_time",  "")

        run_days  = self._calc_run_days(start_str, stop_str)
        is_active = not bool(stop_str)

        item = FacebookAdItem()
        item["advertiser_name"]     = ad.get("page_name") or ad.get("advertiser", {}).get("name", "")
        item["page_id"]             = str(ad.get("page_id", ""))
        item["ad_id"]               = str(ad.get("ad_archive_id", ""))
        item["ad_creative_body"]    = ad.get("ad_creative_body") or ad.get("body", {}).get("text", "")
        item["ad_delivery_start"]   = start_str
        item["ad_delivery_stop"]    = stop_str
        item["is_active"]           = is_active
        item["run_days"]            = run_days
        item["estimated_spend"]     = self._spend_range(ad)
        item["impressions_range"]   = str(ad.get("impressions", {}) or "")
        item["currency"]            = ad.get("currency", "RON")
        item["country"]             = "RO"
        item["ad_category"]         = industry
        item["landing_url"]         = ad.get("snapshot", {}).get("link_url", "")
        item["advertiser_website"]  = ad.get("page_website", "")
        item["industry_tag"]        = industry
        item["budget_signal"]       = self._budget_signal(run_days, is_active)
        item["source"]              = self.name
        item["scraped_at"]          = datetime.now(timezone.utc).isoformat()
        return item

    def _extract_from_html(self, response, query, industry):
        """HTML fallback when JSON extraction finds nothing."""
        cards = response.css(
            "[data-testid='ad-library-result'], "
            "[class*='AdLibraryResult'], "
            "div[role='article']"
        )
        self.logger.info(f"[facebook_ads] HTML fallback — {len(cards)} cards for '{query}'")

        for card in cards:
            name = self._clean(card.css(
                "[data-testid='page-name'] ::text, "
                "[class*='page-name'] ::text, "
                "h2 ::text, strong ::text"
            ).get())
            if not name:
                continue

            body = " ".join(card.css(
                "[data-testid='ad-card-body'] ::text, "
                "[class*='text'] ::text"
            ).getall()[:5])

            start = self._clean(card.css("[class*='start-date'] ::text, time::attr(datetime)").get())
            run_days = self._calc_run_days(start, None)

            item = FacebookAdItem()
            item["advertiser_name"]   = name
            item["page_id"]           = ""
            item["ad_id"]             = ""
            item["ad_creative_body"]  = self._clean(body) or ""
            item["ad_delivery_start"] = start or ""
            item["ad_delivery_stop"]  = None
            item["is_active"]         = True
            item["run_days"]          = run_days
            item["estimated_spend"]   = ""
            item["impressions_range"] = ""
            item["currency"]          = "RON"
            item["country"]           = "RO"
            item["ad_category"]       = industry
            item["landing_url"]       = card.css("a::attr(href)").get() or ""
            item["advertiser_website"]= ""
            item["industry_tag"]      = industry
            item["budget_signal"]     = self._budget_signal(run_days, True)
            item["source"]            = self.name
            item["scraped_at"]        = datetime.now(timezone.utc).isoformat()
            yield item

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _calc_run_days(self, start_str, stop_str):
        """How many days has this ad been / was it running?"""
        if not start_str:
            return None
        try:
            start = datetime.fromisoformat(start_str.replace("Z", "+00:00")).date()
            end   = (datetime.fromisoformat(stop_str.replace("Z", "+00:00")).date()
                     if stop_str else date.today())
            return (end - start).days
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _spend_range(ad):
        spend = ad.get("spend", {})
        if isinstance(spend, dict):
            lo = spend.get("lower_bound", "")
            hi = spend.get("upper_bound", "")
            return f"{lo}-{hi}" if lo or hi else ""
        return str(spend) if spend else ""

    @staticmethod
    def _budget_signal(run_days, is_active):
        if not run_days:
            return "unknown"
        if is_active and run_days >= 60:
            return "confirmed_spender"   # 2+ months active = committed budget
        if is_active and run_days >= 14:
            return "active"
        return "testing"

    @staticmethod
    def _clean(text):
        if not text:
            return None
        return re.sub(r"\s+", " ", text).strip() or None

    def handle_error(self, failure):
        self.logger.warning(f"[facebook_ads] Failed: {failure.request.url} — {failure.value}")
