"""
Spider: competitor_pricing
Target: Romanian web agencies and freelancer profiles
Purpose: Build a pricing matrix to understand market averages and
         identify the positioning gap Seek Digital should own.

Run locally:
    scrapy crawl competitor_pricing -o competitors.csv

Zyte Cloud schedule: weekly (prices change slowly)
"""
import re
import scrapy
from datetime import datetime, timezone
from urllib.parse import urljoin

from seek_intelligence.items import CompetitorItem


# ── Seed URLs — top Romanian web agencies (expand this list over time) ────────
# Sources: Google "agentie web Romania", Clutch.co/ro, local directories
COMPETITOR_SEEDS = [
    # Format: (url, agency_name, city)
    # Direct agency URLs
    ("https://www.gomag.ro",         "Gomag",          "Cluj-Napoca"),
    ("https://www.webdesign.ro",     "WebDesign RO",   "Bucuresti"),
    ("https://www.qds.ro",           "QDS",            "Bucuresti"),
    ("https://www.noblecode.ro",     "Noble Code",     "Cluj-Napoca"),
    ("https://www.iwebconsult.ro",   "iWebConsult",    "Bucuresti"),
    ("https://www.andipixel.ro",     "AndiPixel",      "Iasi"),
    ("https://www.creativeedge.ro",  "Creative Edge",  "Iasi"),
    ("https://www.optimweb.ro",      "OptimWeb",       "Timisoara"),
    ("https://www.magnet.ro",        "Magnet",         "Bucuresti"),
    ("https://www.webstyler.ro",     "WebStyler",      "Timisoara"),
    ("https://www.netopia.ro",       "Netopia",        "Bucuresti"),
    ("https://www.simplenet.ro",     "SimpleNet",      "Cluj-Napoca"),
    # Add more as you discover them
]

# Clutch directory for Romanian agencies
CLUTCH_SEEDS = [
    "https://clutch.co/ro/web-designers",
    "https://clutch.co/ro/agencies/digital-marketing",
]

# Pricing-related URL path patterns to look for on agency sites
PRICING_PATH_PATTERNS = [
    "/preturi", "/servicii", "/pachete", "/tarife",
    "/pricing", "/services", "/packages", "/cost",
    "/web-design-preturi",
]

# Patterns to detect price values in Romanian text
PRICE_PATTERN = re.compile(r"(\d[\d.,]+)\s*(lei|ron|eur|€|euro)", re.IGNORECASE)
MONTHLY_PATTERN = re.compile(r"(\d[\d.,]+)\s*(lei|ron|eur|€|euro)\s*/\s*(luna|lună|month|mo\.?)", re.IGNORECASE)


class CompetitorPricingSpider(scrapy.Spider):
    name = "competitor_pricing"

    custom_settings = {
        "ZYTE_API_DEFAULT_PARAMS": {
            "browserHtml": True,
            "geolocation": "RO",
            "device":      "desktop",
        },
        "DOWNLOAD_DELAY": 3,
        "DEPTH_LIMIT": 2,   # homepage + one pricing/services page
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    def __init__(self, include_clutch=True, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.include_clutch = str(include_clutch).lower() != "false"

    def start_requests(self):
        # Scrape known competitor homepages
        for url, name, city in COMPETITOR_SEEDS:
            yield scrapy.Request(
                url,
                callback=self.parse_homepage,
                meta={
                    "agency_name": name,
                    "city":        city,
                    "zyte_api":    {"browserHtml": True, "geolocation": "RO"},
                },
                errback=self.handle_error,
            )

        # Scrape Clutch directory for more agencies
        if self.include_clutch:
            for url in CLUTCH_SEEDS:
                yield scrapy.Request(
                    url,
                    callback=self.parse_clutch_directory,
                    meta={"zyte_api": {"browserHtml": True, "geolocation": "US"}},
                    errback=self.handle_error,
                )

    # ── Homepage parsing ──────────────────────────────────────────────────────

    def parse_homepage(self, response):
        agency_name = response.meta.get("agency_name", self._extract_agency_name(response))
        city        = response.meta.get("city", "")

        item = CompetitorItem()
        item["agency_name"]   = agency_name
        item["agency_url"]    = response.url
        item["city"]          = city
        item["source"]        = self.name
        item["scraped_at"]    = datetime.now(timezone.utc).isoformat()
        item["pricing_visible"] = False   # default; may be updated

        # Extract headline / value prop from homepage
        headline = (
            response.css("h1 ::text").get()
            or response.css("[class*='hero'] h2 ::text").get()
            or response.css("header h2 ::text").get()
        )
        item["positioning_copy"] = self._clean(headline)

        # Detect guarantee mentions
        page_text = " ".join(response.css("body ::text").getall()).lower()
        item["guarantee_mentioned"] = any(
            kw in page_text for kw in ["garantie", "garantat", "guarantee", "money back", "ramburs"]
        )

        # Services detection from nav / footer
        item["services_offered"] = self._extract_services(page_text)

        # Check for pricing on homepage itself
        prices = self._extract_prices(response)
        if prices:
            item.update(prices)
            item["pricing_visible"] = True

        # Try to find a pricing/services subpage
        pricing_url = self._find_pricing_url(response)
        if pricing_url:
            yield scrapy.Request(
                pricing_url,
                callback=self.parse_pricing_page,
                meta={
                    "item":    item,
                    "zyte_api": {"browserHtml": True, "geolocation": "RO"},
                },
                errback=self.handle_error,
            )
        else:
            yield item

    # ── Pricing page ──────────────────────────────────────────────────────────

    def parse_pricing_page(self, response):
        item   = response.meta["item"]
        prices = self._extract_prices(response)

        if prices:
            item.update(prices)
            item["pricing_visible"] = True

        # Raw pricing text for manual review
        pricing_sections = response.css(
            "[class*='pric'], [class*='pachet'], [class*='tarif'], "
            "[id*='pric'], [id*='pachet'], [class*='plan']"
        )
        raw_texts = " | ".join(
            self._clean(" ".join(s.css("::text").getall())) or ""
            for s in pricing_sections[:5]
        )
        item["pricing_raw"] = raw_texts[:2000]  # cap at 2k chars

        yield item

    # ── Clutch directory ──────────────────────────────────────────────────────

    def parse_clutch_directory(self, response):
        """Extract agency listing from Clutch.co directory."""
        companies = response.css(
            "li[data-og_uid], "
            "[class*='company_info'], "
            "article[class*='provider']"
        )
        self.logger.info(f"[competitor_pricing] Clutch: {len(companies)} companies on {response.url}")

        for company in companies:
            name    = self._clean(company.css("h3 ::text, [class*='company-name'] ::text").get())
            url     = company.css("a[class*='website']::attr(href), a[href*='http']::attr(href)").get()
            rating  = self._clean(company.css("[class*='rating'] ::text, [class*='stars'] ::text").get())
            reviews = self._clean(company.css("[class*='review-count'] ::text").get())
            city    = self._clean(company.css("[class*='location'] ::text").get())

            if not name or not url:
                continue

            item = CompetitorItem()
            item["agency_name"]    = name
            item["agency_url"]     = url
            item["city"]           = city or ""
            item["clutch_rating"]  = self._to_float(rating)
            item["clutch_reviews"] = self._to_int(reviews)
            item["source"]         = f"{self.name}/clutch"
            item["scraped_at"]     = datetime.now(timezone.utc).isoformat()

            # Follow to their homepage for full data
            yield scrapy.Request(
                url,
                callback=self.parse_homepage,
                meta={
                    "agency_name": name,
                    "city":        city or "",
                    "zyte_api":    {"browserHtml": True, "geolocation": "RO"},
                },
                errback=self.handle_error,
            )

        # Paginate through Clutch directory
        next_page = response.css("a[rel='next']::attr(href), a.next::attr(href)").get()
        if next_page:
            yield response.follow(
                next_page,
                callback=self.parse_clutch_directory,
                meta={"zyte_api": {"browserHtml": True}},
                errback=self.handle_error,
            )

    # ── Price extraction helpers ───────────────────────────────────────────────

    def _extract_prices(self, response):
        """Find and parse price mentions on the page."""
        page_text = " ".join(response.css("body ::text").getall())
        matches   = PRICE_PATTERN.findall(page_text)
        monthly   = MONTHLY_PATTERN.findall(page_text)

        if not matches:
            return {}

        # Convert all found prices to integers (normalize EUR -> LEI roughly x5)
        lei_values = []
        for amount, currency in matches:
            val = self._parse_amount(amount)
            if val is None:
                continue
            if currency.lower() in ("eur", "€", "euro"):
                val = val * 5   # rough conversion for comparison
            lei_values.append(val)

        if not lei_values:
            return {}

        lei_values.sort()
        result = {}

        if len(lei_values) >= 1:
            result["entry_price"]   = lei_values[0]
        if len(lei_values) >= 2:
            result["premium_price"] = lei_values[-1]
        if len(lei_values) >= 3:
            result["mid_price"]     = lei_values[len(lei_values) // 2]

        # Monthly retainer
        if monthly:
            val = self._parse_amount(monthly[0][0])
            if val:
                currency = monthly[0][1].lower()
                if currency in ("eur", "€", "euro"):
                    val = val * 5
                result["monthly_retainer"] = val

        return result

    def _find_pricing_url(self, response):
        """Try to find a pricing/services link on the homepage."""
        all_links = response.css("a[href]")
        for link in all_links:
            href = link.attrib.get("href", "")
            text = " ".join(link.css("::text").getall()).lower()
            if any(pattern.strip("/") in href.lower() for pattern in PRICING_PATH_PATTERNS):
                return urljoin(response.url, href)
            if any(kw in text for kw in ["preturi", "pachete", "tarife", "pricing", "servicii"]):
                return urljoin(response.url, href)
        return None

    def _extract_services(self, page_text):
        """Detect which services the agency offers from keyword matching."""
        services = []
        checks = {
            "web design":       ["web design", "website", "site"],
            "ecommerce":        ["magazin online", "ecommerce", "woocommerce", "shopify"],
            "seo":              ["seo", "optimizare motoare"],
            "google ads":       ["google ads", "ppc", "adwords"],
            "meta ads":         ["facebook ads", "meta ads", "instagram ads"],
            "social media":     ["social media", "retele sociale", "instagram"],
            "branding":         ["branding", "logo", "identitate vizuala"],
            "mobile app":       ["aplicatie mobila", "mobile app", "android", "ios"],
        }
        for service, keywords in checks.items():
            if any(kw in page_text for kw in keywords):
                services.append(service)
        return services

    def _extract_agency_name(self, response):
        return (
            self._clean(response.css("title::text").get() or "")
            .split("|")[0].split("–")[0].strip()
        )

    @staticmethod
    def _parse_amount(text):
        try:
            return int(float(text.replace(".", "").replace(",", ".")))
        except (ValueError, AttributeError):
            return None

    @staticmethod
    def _to_float(text):
        if not text:
            return None
        m = re.search(r"[\d.]+", text)
        try:
            return float(m.group()) if m else None
        except ValueError:
            return None

    @staticmethod
    def _to_int(text):
        if not text:
            return None
        m = re.search(r"\d+", text)
        return int(m.group()) if m else None

    @staticmethod
    def _clean(text):
        if not text:
            return None
        return re.sub(r"\s+", " ", text).strip() or None

    def handle_error(self, failure):
        self.logger.warning(f"[competitor_pricing] Failed: {failure.request.url} — {failure.value}")
