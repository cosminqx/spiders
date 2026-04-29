"""
Airtable Exporter — push scraped + scored items to Airtable
Usage: add AIRTABLE_PIPELINE to ITEM_PIPELINES in settings or pass via CLI

This replaces the manual CSV → Airtable import step once you're ready
to automate the full pipeline.

Prerequisites:
    pip install pyairtable
    Set AIRTABLE_API_KEY, AIRTABLE_BASE_ID in .env
"""
import os
import logging
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

try:
    from pyairtable import Api as AirtableApi
    AIRTABLE_AVAILABLE = True
except ImportError:
    AIRTABLE_AVAILABLE = False
    logger.warning("[airtable_exporter] pyairtable not installed — pip install pyairtable")

from itemadapter import ItemAdapter
from seek_intelligence.items import BusinessItem, FacebookAdItem, CompetitorItem


class AirtablePipeline:
    """
    Optional pipeline — sends items to Airtable after scoring.
    Enable by adding to ITEM_PIPELINES at priority 400:
        "seek_intelligence.exporters.airtable_exporter.AirtablePipeline": 400,
    """

    # Map item type → Airtable table name (match exactly what you named them)
    TABLE_MAP = {
        "BusinessItem":    "Business Registry",
        "FacebookAdItem":  "Ad Signals",
        "CompetitorItem":  "Competitor Intelligence",
    }

    def __init__(self):
        self.api_key = os.getenv("AIRTABLE_API_KEY", "")
        self.base_id = os.getenv("AIRTABLE_BASE_ID", "")
        self._client  = None
        self._tables  = {}

    @classmethod
    def from_crawler(cls, crawler):
        return cls()

    def open_spider(self, spider):
        if not AIRTABLE_AVAILABLE:
            spider.logger.warning("[airtable] pyairtable missing — disabling Airtable export")
            return
        if not self.api_key or not self.base_id:
            spider.logger.warning("[airtable] Missing AIRTABLE_API_KEY or AIRTABLE_BASE_ID — disabling")
            return
        self._client = AirtableApi(self.api_key)
        spider.logger.info("[airtable] Connected — will push to base " + self.base_id)

    def process_item(self, item, spider):
        if not self._client:
            return item

        item_type = type(item).__name__
        table_name = self.TABLE_MAP.get(item_type)
        if not table_name:
            return item

        if table_name not in self._tables:
            self._tables[table_name] = self._client.table(self.base_id, table_name)

        fields = self._to_airtable_fields(item)
        try:
            self._tables[table_name].create(fields)
        except Exception as e:
            spider.logger.warning(f"[airtable] Failed to insert {item_type}: {e}")

        return item

    # ── Field mapping ─────────────────────────────────────────────────────────

    def _to_airtable_fields(self, item):
        adapter = ItemAdapter(item)

        if isinstance(item, BusinessItem):
            return {
                "Name":           adapter.get("name", ""),
                "Industry":       adapter.get("industry", ""),
                "City":           adapter.get("city", ""),
                "Phone":          adapter.get("phone", ""),
                "Website":        adapter.get("website_url", ""),
                "Has Website":    adapter.get("has_website", False),
                "Lead Score":     adapter.get("lead_score", 0),
                "Lead Tier":      adapter.get("lead_tier", "cold"),
                "Review Count":   adapter.get("review_count") or 0,
                "Has Facebook":   adapter.get("has_facebook", False),
                "Has Instagram":  adapter.get("has_instagram", False),
                "Source":         adapter.get("source", ""),
                "Scraped At":     adapter.get("scraped_at", ""),
                "Status":         "New",   # for Tudor's outreach tracking
            }

        if isinstance(item, FacebookAdItem):
            return {
                "Advertiser":     adapter.get("advertiser_name", ""),
                "Is Active":      adapter.get("is_active", False),
                "Run Days":       adapter.get("run_days") or 0,
                "Budget Signal":  adapter.get("budget_signal", ""),
                "Industry":       adapter.get("industry_tag", ""),
                "Landing URL":    adapter.get("landing_url", ""),
                "Ad Creative":    (adapter.get("ad_creative_body") or "")[:500],
                "Scraped At":     adapter.get("scraped_at", ""),
            }

        if isinstance(item, CompetitorItem):
            return {
                "Agency Name":      adapter.get("agency_name", ""),
                "URL":              adapter.get("agency_url", ""),
                "City":             adapter.get("city", ""),
                "Entry Price":      adapter.get("entry_price") or 0,
                "Mid Price":        adapter.get("mid_price") or 0,
                "Premium Price":    adapter.get("premium_price") or 0,
                "Monthly Retainer": adapter.get("monthly_retainer") or 0,
                "Pricing Visible":  adapter.get("pricing_visible", False),
                "Services":         ", ".join(adapter.get("services_offered") or []),
                "Positioning":      adapter.get("positioning_copy", ""),
                "Guarantee":        adapter.get("guarantee_mentioned", False),
                "Scraped At":       adapter.get("scraped_at", ""),
            }

        return dict(ItemAdapter(item).asdict())
