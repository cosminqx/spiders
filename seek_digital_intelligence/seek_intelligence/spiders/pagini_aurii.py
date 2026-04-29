"""
Spider: pagini_aurii
Target: https://www.paginiaurii.ro
Purpose: Collect Romanian SME listings by industry + city.
         Extracts business name, phone, address, website presence —
         the raw material for lead scoring.

Run locally:
    scrapy crawl pagini_aurii -a industry=restaurante -a city=iasi -o out.csv

Zyte Cloud schedule: daily, 02:00 EET
"""
import re
import scrapy
from datetime import datetime, timezone
from urllib.parse import urljoin, urlencode

from seek_intelligence.items import BusinessItem


# Industries Seek Digital targets (CAEN-aligned Romanian terms)
DEFAULT_INDUSTRIES = [
    "restaurante",
    "cafenele",
    "baruri",
    "saloane-infrumusetare",
    "cabinete-stomatologice",
    "cabinete-medicale",
    "service-auto",
    "fitness-aerobic",
    "constructii",
    "imobiliare",
]

# Top Romanian cities by SME density (>50k population per your plan)
DEFAULT_CITIES = [
    "iasi",
    "cluj-napoca",
    "timisoara",
    "brasov",
    "constanta",
    "craiova",
    "galati",
    "ploiesti",
    "oradea",
    "sibiu",
    "bacau",
    "pitesti",
    "bucuresti",
]


class PaginiAuriiSpider(scrapy.Spider):
    name = "pagini_aurii"
    allowed_domains = ["paginiaurii.ro"]

    # Spider-level Zyte API config: use browser rendering for JS-heavy pages
    custom_settings = {
        "ZYTE_API_DEFAULT_PARAMS": {
            "browserHtml": True,          # full JS rendering
            "geolocation": "RO",          # Romanian IP
            "device": "desktop",
        },
        "DOWNLOAD_DELAY": 2.5,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 1,
    }

    def __init__(self, industry=None, city=None, max_pages=20, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Accept comma-separated lists or single values from CLI / Zyte schedule
        self.industries = [i.strip() for i in industry.split(",")] if industry else DEFAULT_INDUSTRIES
        self.cities      = [c.strip() for c in city.split(",")]    if city      else DEFAULT_CITIES
        self.max_pages   = int(max_pages)
        self.seen_phones = set()   # light dedup within a run

    def start_requests(self):
        for city in self.cities:
            for industry in self.industries:
                url = f"https://www.paginiaurii.ro/{industry}/{city}/"
                yield scrapy.Request(
                    url,
                    callback=self.parse_listing,
                    meta={
                        "city":     city,
                        "industry": industry,
                        "page":     1,
                        "zyte_api": {"browserHtml": True, "geolocation": "RO"},
                    },
                    errback=self.handle_error,
                )

    # ── Listing page ──────────────────────────────────────────────────────────

    def parse_listing(self, response):
        city     = response.meta["city"]
        industry = response.meta["industry"]
        page     = response.meta["page"]

        listings = response.css("div.searchResultItem, div.listing-item, article.result")

        if not listings:
            # Fallback selector — pagini aurii sometimes changes class names
            listings = response.css("[class*='result'], [class*='listing'], [class*='company']")

        self.logger.info(
            f"[pagini_aurii] {city}/{industry} p{page} — {len(listings)} listings"
        )

        for listing in listings:
            yield from self.parse_listing_card(listing, city, industry)

        # ── Pagination ────────────────────────────────────────────────────────
        if page < self.max_pages:
            next_url = response.css("a.next-page::attr(href), a[rel='next']::attr(href)").get()
            if next_url:
                yield response.follow(
                    next_url,
                    callback=self.parse_listing,
                    meta={
                        "city":     city,
                        "industry": industry,
                        "page":     page + 1,
                        "zyte_api": {"browserHtml": True, "geolocation": "RO"},
                    },
                    errback=self.handle_error,
                )

    def parse_listing_card(self, card, city, industry):
        """Extract data from a single business card on the listing page."""
        name    = self._clean(card.css("[class*='name'] ::text, h2 ::text, h3 ::text").get())
        phone   = self._clean(card.css("[class*='phone'] ::text, [href^='tel:'] ::text").get())
        address = self._clean(card.css("[class*='address'] ::text, [class*='street'] ::text").get())
        website = card.css("[class*='website']::attr(href), a[class*='web']::attr(href)").get()
        detail_url = card.css("a[class*='title']::attr(href), h2 a::attr(href), h3 a::attr(href)").get()

        if not name:
            return

        # Light dedup on phone within this crawl session
        if phone and phone in self.seen_phones:
            return
        if phone:
            self.seen_phones.add(phone)

        item = BusinessItem()
        item["name"]        = name
        item["industry"]    = industry
        item["city"]        = city.replace("-", " ").title()
        item["county"]      = ""   # populated below if detail page is fetched
        item["address"]     = address or ""
        item["phone"]       = phone or ""
        item["website_url"] = website
        item["has_website"] = bool(website)
        item["source"]      = self.name
        item["scraped_at"]  = datetime.now(timezone.utc).isoformat()

        # If there's a detail page, fetch it to enrich the item
        if detail_url:
            detail_url = urljoin(response.url, detail_url)
            yield scrapy.Request(
                detail_url,
                callback=self.parse_detail,
                meta={
                    "item":    item,
                    "zyte_api": {"browserHtml": True, "geolocation": "RO"},
                },
                errback=self.handle_error,
            )
        else:
            yield item

    # ── Detail page ───────────────────────────────────────────────────────────

    def parse_detail(self, response):
        item = response.meta["item"]

        # Enrich from detail page
        website = (
            response.css("a[class*='website']::attr(href)").get()
            or response.css("a[href^='http']:not([href*='paginiaurii'])::attr(href)").get()
        )
        if website and not item.get("website_url"):
            item["website_url"] = website
            item["has_website"] = True

        # Try to pull social links
        all_links = response.css("a::attr(href)").getall()
        item["has_facebook"]  = any("facebook.com" in l for l in all_links)
        item["has_instagram"] = any("instagram.com" in l for l in all_links)

        # County from breadcrumb or meta
        county = self._clean(response.css("span.county ::text, [class*='county'] ::text").get())
        item["county"] = county or ""

        # Review signals
        rating = self._clean(response.css("[class*='rating'] ::text, [itemprop='ratingValue'] ::text").get())
        count  = self._clean(response.css("[class*='review'] ::text, [itemprop='reviewCount'] ::text").get())
        item["avg_rating"]   = self._to_float(rating)
        item["review_count"] = self._to_int(count)
        item["has_google_biz"] = False   # populated by website audit spider

        yield item

    # ── Helpers ───────────────────────────────────────────────────────────────

    def handle_error(self, failure):
        self.logger.warning(f"[pagini_aurii] Request failed: {failure.request.url} — {failure.value}")

    @staticmethod
    def _clean(text):
        if not text:
            return None
        return re.sub(r"\s+", " ", text).strip() or None

    @staticmethod
    def _to_float(text):
        if not text:
            return None
        m = re.search(r"[\d.,]+", text.replace(",", "."))
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
