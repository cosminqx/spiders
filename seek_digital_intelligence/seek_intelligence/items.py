"""
Seek Digital Intelligence — Item definitions
One item class per data domain. All fields are documented with what
they mean for the lead-scoring and outreach workflows.
"""
import scrapy


# ─────────────────────────────────────────────────────────────────────────────
# Business / Lead item (Pagini Aurii, Google Maps)
# ─────────────────────────────────────────────────────────────────────────────

class BusinessItem(scrapy.Item):
    # Identity
    name            = scrapy.Field()   # business name
    industry        = scrapy.Field()   # category from directory
    city            = scrapy.Field()   # city
    county          = scrapy.Field()   # judet
    address         = scrapy.Field()   # full street address
    phone           = scrapy.Field()   # primary phone

    # Digital presence — the core scoring signals
    website_url     = scrapy.Field()   # raw URL or None
    has_website     = scrapy.Field()   # bool
    website_year    = scrapy.Field()   # copyright year in footer (staleness signal)
    is_mobile_ok    = scrapy.Field()   # bool — viewport meta tag present
    has_ssl         = scrapy.Field()   # bool
    cms_detected    = scrapy.Field()   # WordPress / Wix / custom etc

    # Social signals
    has_facebook    = scrapy.Field()   # bool
    has_instagram   = scrapy.Field()   # bool
    has_google_biz  = scrapy.Field()   # bool — Google Business profile found
    review_count    = scrapy.Field()   # int — proxy for business activity
    avg_rating      = scrapy.Field()   # float

    # Lead scoring (computed in pipeline)
    lead_score      = scrapy.Field()   # int 0–100
    lead_tier       = scrapy.Field()   # "hot" / "warm" / "cold"
    score_breakdown = scrapy.Field()   # dict with per-signal points

    # Meta
    source          = scrapy.Field()   # spider name
    scraped_at      = scrapy.Field()   # ISO timestamp


# ─────────────────────────────────────────────────────────────────────────────
# Facebook Ad Library item
# ─────────────────────────────────────────────────────────────────────────────

class FacebookAdItem(scrapy.Item):
    advertiser_name     = scrapy.Field()   # page / business name
    page_id             = scrapy.Field()
    ad_id               = scrapy.Field()
    ad_creative_body    = scrapy.Field()   # ad copy text
    ad_delivery_start   = scrapy.Field()   # when ad started running
    ad_delivery_stop    = scrapy.Field()   # None if still active
    is_active           = scrapy.Field()   # bool
    run_days            = scrapy.Field()   # int — how long ad has been running
    estimated_spend     = scrapy.Field()   # spend range string from FB
    impressions_range   = scrapy.Field()
    currency            = scrapy.Field()
    country             = scrapy.Field()
    ad_category         = scrapy.Field()
    landing_url         = scrapy.Field()   # where the ad clicks to
    advertiser_website  = scrapy.Field()   # from page info
    industry_tag        = scrapy.Field()   # our classification

    # Lead signal: running ads + bad website = hot lead
    budget_signal       = scrapy.Field()   # "confirmed_spender" / "active" / "testing"

    source              = scrapy.Field()
    scraped_at          = scrapy.Field()


# ─────────────────────────────────────────────────────────────────────────────
# Competitor pricing item
# ─────────────────────────────────────────────────────────────────────────────

class CompetitorItem(scrapy.Item):
    agency_name         = scrapy.Field()
    agency_url          = scrapy.Field()
    city                = scrapy.Field()
    team_size_signal    = scrapy.Field()   # "solo" / "small" / "mid" / "large"
    founded_year        = scrapy.Field()

    # Pricing — we store all tiers we can find
    pricing_visible     = scrapy.Field()   # bool — do they publish prices?
    entry_price         = scrapy.Field()   # int (lei)
    mid_price           = scrapy.Field()   # int (lei)
    premium_price       = scrapy.Field()   # int (lei)
    monthly_retainer    = scrapy.Field()   # int (lei/month)
    pricing_raw         = scrapy.Field()   # raw text scraped from pricing page

    # Positioning
    services_offered    = scrapy.Field()   # list of services
    specialization      = scrapy.Field()   # industry focus if any
    positioning_copy    = scrapy.Field()   # their headline / value prop
    guarantee_mentioned = scrapy.Field()   # bool — do they offer a guarantee?

    # Competitive signals
    clutch_rating       = scrapy.Field()
    clutch_reviews      = scrapy.Field()
    google_reviews      = scrapy.Field()
    portfolio_count     = scrapy.Field()

    source              = scrapy.Field()
    scraped_at          = scrapy.Field()


# ─────────────────────────────────────────────────────────────────────────────
# Website audit item (secondary crawl of discovered websites)
# ─────────────────────────────────────────────────────────────────────────────

class WebsiteAuditItem(scrapy.Item):
    url                 = scrapy.Field()
    business_name       = scrapy.Field()
    http_status         = scrapy.Field()   # 200 / 404 / 500 etc
    load_ok             = scrapy.Field()   # bool
    has_viewport_meta   = scrapy.Field()   # mobile-friendly signal
    has_ssl             = scrapy.Field()
    copyright_year      = scrapy.Field()   # extracted from footer
    cms_detected        = scrapy.Field()   # WordPress / Wix / Squarespace etc
    has_analytics       = scrapy.Field()   # GA / FB pixel present
    has_contact_form    = scrapy.Field()
    page_title          = scrapy.Field()
    meta_description    = scrapy.Field()
    last_modified       = scrapy.Field()   # HTTP header

    staleness_signal    = scrapy.Field()   # "outdated" / "recent" / "unknown"
    audit_score         = scrapy.Field()   # 0–10 quick quality score

    source              = scrapy.Field()
    scraped_at          = scrapy.Field()
