"""
Seek Digital Intelligence — Item Pipelines
Runs on every scraped item in order:
  1. ValidatePipeline     — drops junk / incomplete items
  2. LeadScoringPipeline  — computes lead_score + lead_tier for BusinessItems
  3. DeduplicationPipeline — drops exact duplicates within a session
"""
from itemadapter import ItemAdapter
from seek_intelligence.items import BusinessItem, FacebookAdItem, WebsiteAuditItem


# ─────────────────────────────────────────────────────────────────────────────
# 1. Validation
# ─────────────────────────────────────────────────────────────────────────────

class ValidatePipeline:
    """Drop items that are clearly incomplete or useless."""

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if isinstance(item, BusinessItem):
            if not adapter.get("name"):
                raise DropItem(f"Missing name: {item}")
            if not adapter.get("city"):
                raise DropItem(f"Missing city: {item}")

        if isinstance(item, FacebookAdItem):
            if not adapter.get("advertiser_name"):
                raise DropItem(f"Missing advertiser: {item}")

        if isinstance(item, WebsiteAuditItem):
            if not adapter.get("url"):
                raise DropItem(f"Missing URL: {item}")

        return item


# ─────────────────────────────────────────────────────────────────────────────
# 2. Lead Scoring  (applies only to BusinessItem)
# ─────────────────────────────────────────────────────────────────────────────

class LeadScoringPipeline:
    """
    Score each business lead from 0–100.
    Higher score = higher priority for Seek Digital outreach.

    Scoring rationale (mirrors the system from the strategy doc):
      - Running active ads         +30   confirmed digital budget
      - No website                 +25   obvious gap we can fill
      - Outdated website           +15   easy upgrade sale
      - No mobile optimisation     +15   measurable problem
      - Good review count          +10   active business, paying customers
      - Has Facebook/Instagram     + 5   already cares about digital
      - No analytics               + 5   they're flying blind — we can fix that
    """

    SCORE_TABLE = {
        "no_website":       25,
        "outdated_site":    15,
        "no_mobile":        15,
        "high_reviews":     10,
        "has_social":        5,
        "no_analytics":      5,
        # Note: "running_ads" (+30) is joined from facebook_ads data post-scrape
        # in Airtable/Make.com — we can't compute it here without cross-referencing
    }

    def process_item(self, item, spider):
        if not isinstance(item, BusinessItem):
            return item

        adapter   = ItemAdapter(item)
        score     = 0
        breakdown = {}

        # No website at all
        if not adapter.get("has_website"):
            score               += self.SCORE_TABLE["no_website"]
            breakdown["no_website"] = self.SCORE_TABLE["no_website"]

        # Outdated website (populated by website_audit spider or extracted from listing)
        staleness = adapter.get("staleness_signal")
        if staleness == "outdated":
            score                   += self.SCORE_TABLE["outdated_site"]
            breakdown["outdated_site"] = self.SCORE_TABLE["outdated_site"]

        # No mobile optimisation
        if adapter.get("has_website") and adapter.get("is_mobile_ok") is False:
            score               += self.SCORE_TABLE["no_mobile"]
            breakdown["no_mobile"] = self.SCORE_TABLE["no_mobile"]

        # Active business signal: 20+ reviews
        review_count = adapter.get("review_count") or 0
        if review_count >= 20:
            score                   += self.SCORE_TABLE["high_reviews"]
            breakdown["high_reviews"] = self.SCORE_TABLE["high_reviews"]

        # Has at least one social presence
        has_social = adapter.get("has_facebook") or adapter.get("has_instagram")
        if has_social:
            score               += self.SCORE_TABLE["has_social"]
            breakdown["has_social"] = self.SCORE_TABLE["has_social"]

        # No analytics (website exists but they can't measure results)
        if adapter.get("has_website") and adapter.get("has_analytics") is False:
            score                   += self.SCORE_TABLE["no_analytics"]
            breakdown["no_analytics"] = self.SCORE_TABLE["no_analytics"]

        adapter["lead_score"]     = min(score, 100)
        adapter["score_breakdown"] = breakdown
        adapter["lead_tier"]      = self._tier(score)

        return item

    @staticmethod
    def _tier(score):
        if score >= 50:
            return "hot"    # priority outreach — Tudor calls these first
        if score >= 25:
            return "warm"   # follow up after hot
        return "cold"


# ─────────────────────────────────────────────────────────────────────────────
# 3. Deduplication
# ─────────────────────────────────────────────────────────────────────────────

class DeduplicationPipeline:
    """
    Drop duplicate items within a single spider run.
    Key: (name + city) for BusinessItems, ad_id for FacebookAdItems, url for audits.
    Cross-run deduplication is handled in Airtable via the phone / URL unique field.
    """

    def __init__(self):
        self.seen = set()

    def process_item(self, item, spider):
        adapter = ItemAdapter(item)

        if isinstance(item, BusinessItem):
            key = (
                (adapter.get("name") or "").lower().strip(),
                (adapter.get("city") or "").lower().strip(),
            )
        elif isinstance(item, FacebookAdItem):
            key = adapter.get("ad_id") or adapter.get("advertiser_name", "")
        elif isinstance(item, WebsiteAuditItem):
            key = adapter.get("url", "")
        else:
            return item

        if key in self.seen:
            raise DropItem(f"Duplicate: {key}")

        self.seen.add(key)
        return item


# ─────────────────────────────────────────────────────────────────────────────
# Utility
# ─────────────────────────────────────────────────────────────────────────────

class DropItem(Exception):
    """Raised to silently drop an item from the pipeline."""
    pass


# Monkey-patch Scrapy's DropItem so our custom one is compatible
try:
    from scrapy.exceptions import DropItem as ScrapyDropItem
    DropItem = ScrapyDropItem
except ImportError:
    pass
