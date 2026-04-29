# Sample Spider Outputs

## 1. pagini_aurii — Lead Discovery (Romanian SMEs)

```json
[
  {
    "name": "Restaurant Casa Veche",
    "industry": "restaurante",
    "city": "Iasi",
    "county": "Iasi",
    "address": "Str. Sfantului 45, Iasi",
    "phone": "+40232 123456",
    "website_url": "https://casaveche-iasi.ro",
    "has_website": true,
    "website_year": 2019,
    "is_mobile_ok": false,
    "has_ssl": true,
    "cms_detected": "WordPress",
    "has_facebook": true,
    "has_instagram": true,
    "has_google_biz": true,
    "review_count": 87,
    "avg_rating": 4.5,
    "lead_score": 58,
    "lead_tier": "hot",
    "score_breakdown": {
      "outdated_website": 15,
      "not_mobile_optimized": 15,
      "has_reviews": 10,
      "has_social": 5,
      "has_website": 0
    },
    "source": "pagini_aurii",
    "scraped_at": "2026-04-29T17:05:00Z"
  },
  {
    "name": "Salon Frumusete Elena",
    "industry": "saloane-infrumusetare",
    "city": "Iasi",
    "county": "Iasi",
    "address": "Str. Copou 12, Iasi",
    "phone": "+40232 654321",
    "website_url": null,
    "has_website": false,
    "website_year": null,
    "is_mobile_ok": null,
    "has_ssl": null,
    "cms_detected": null,
    "has_facebook": true,
    "has_instagram": true,
    "has_google_biz": false,
    "review_count": 34,
    "avg_rating": 4.8,
    "lead_score": 75,
    "lead_tier": "hot",
    "score_breakdown": {
      "no_website": 25,
      "has_social": 5,
      "has_reviews": 10,
      "has_facebook": 5
    },
    "source": "pagini_aurii",
    "scraped_at": "2026-04-29T17:05:45Z"
  },
  {
    "name": "Cabinet Stomatologic Dr Popescu",
    "industry": "cabinete-stomatologice",
    "city": "Iasi",
    "county": "Iasi",
    "address": "Str. Lascar Catargi 8, Iasi",
    "phone": "+40232 555888",
    "website_url": "https://dentialpopescu.ro",
    "has_website": true,
    "website_year": 2018,
    "is_mobile_ok": true,
    "has_ssl": true,
    "cms_detected": "Custom",
    "has_facebook": false,
    "has_instagram": false,
    "has_google_biz": true,
    "review_count": 156,
    "avg_rating": 4.9,
    "lead_score": 28,
    "lead_tier": "cold",
    "score_breakdown": {
      "outdated_website": 15,
      "has_reviews": 10,
      "has_ssl": 3
    },
    "source": "pagini_aurii",
    "scraped_at": "2026-04-29T17:06:12Z"
  }
]
```

**Key Fields Explained:**
- **lead_score** (0–100): Higher = better lead for Seek Digital to target
- **lead_tier**: "hot" (50+) = call today, "warm" (25–49) = follow up this week, "cold" (<25) = batch outreach
- **website_year**: Year from copyright notice in footer — indicates staleness
- **cms_detected**: WordPress/Wix/Custom — helps with messaging (e.g., "WordPress performance audit")
- **Signals scored**: no website (+25), outdated site (+15), not mobile (+15), social presence (+5), reviews (+10), no analytics (+5), running ads (+30)

---

## 2. facebook_ads — Active Spenders (Budget Signals)

```json
[
  {
    "advertiser_name": "Restaurant Casa Veche",
    "page_id": "1234567890",
    "ad_id": "FB_AD_001",
    "ad_creative_body": "Noi sorturi de vinuri rosii! Rezerva masa astazi - 20% reducere",
    "ad_delivery_start": "2026-04-15",
    "ad_delivery_stop": null,
    "is_active": true,
    "run_days": 14,
    "estimated_spend": "$500-$1000",
    "impressions_range": "10K-50K",
    "currency": "USD",
    "country": "RO",
    "ad_category": "Restaurants & Dining",
    "landing_url": "https://casaveche-iasi.ro/reserve",
    "advertiser_website": "https://casaveche-iasi.ro",
    "industry_tag": "horeca",
    "budget_signal": "active",
    "source": "facebook_ads",
    "scraped_at": "2026-04-29T17:10:00Z"
  },
  {
    "advertiser_name": "AgentieFasadesRO",
    "page_id": "9876543210",
    "ad_id": "FB_AD_002",
    "ad_creative_body": "Renovare fatada? Suntem specialistii! Consultatie GRATUITA",
    "ad_delivery_start": "2026-02-01",
    "ad_delivery_stop": null,
    "is_active": true,
    "run_days": 88,
    "estimated_spend": "$2000-$5000",
    "impressions_range": "100K-1M",
    "currency": "USD",
    "country": "RO",
    "ad_category": "Home Services",
    "landing_url": "https://fasade.example.ro/quote",
    "advertiser_website": "https://fasade.example.ro",
    "industry_tag": "constructii",
    "budget_signal": "confirmed_spender",
    "source": "facebook_ads",
    "scraped_at": "2026-04-29T17:10:32Z"
  }
]
```

**Signal Breakdown:**
- **budget_signal**:
  - `confirmed_spender`: Active 60+ days → has committed budget, serious business
  - `active`: 14–59 days → testing or ongoing campaigns
  - `testing`: <14 days → early-stage experiment

**Lead Quality:** When you see "confirmed_spender" + "no website" or "outdated website" from pagini_aurii, that's your best lead. They have budget and a clear pain point.

---

## 3. competitor_pricing — Romanian Web Agencies

```json
[
  {
    "agency_name": "Web Dynamics Cluj",
    "agency_url": "https://webdynamics.ro",
    "city": "Cluj-Napoca",
    "team_size_signal": "mid",
    "founded_year": 2015,
    "pricing_visible": true,
    "entry_price": 800,
    "mid_price": 2500,
    "premium_price": 6000,
    "monthly_retainer": 1200,
    "pricing_raw": "Website design from 800 RON | Full development 2500-6000 RON | Monthly retainers from 1200 RON",
    "services_offered": [
      "Web Design",
      "Web Development",
      "E-Commerce",
      "SEO",
      "PPC"
    ],
    "specialization": "E-commerce for SMEs",
    "positioning_copy": "We transform businesses with modern, conversion-focused websites",
    "guarantee_mentioned": true,
    "source": "competitor_pricing",
    "scraped_at": "2026-04-29T17:12:00Z"
  },
  {
    "agency_name": "Agentia Digitala Bucuresti",
    "agency_url": "https://agdigi.ro",
    "city": "Bucuresti",
    "team_size_signal": "large",
    "founded_year": 2010,
    "pricing_visible": false,
    "entry_price": null,
    "mid_price": null,
    "premium_price": null,
    "monthly_retainer": null,
    "pricing_raw": "Contact us for a custom quote",
    "services_offered": [
      "Web Design",
      "Branding",
      "Marketing",
      "Mobile Apps",
      "Consulting"
    ],
    "specialization": null,
    "positioning_copy": "Enterprise-grade digital solutions for ambitious brands",
    "guarantee_mentioned": false,
    "source": "competitor_pricing",
    "scraped_at": "2026-04-29T17:12:45Z"
  }
]
```

**Market Intelligence:**
- Entry pricing: RON 800–1500 (typical for basic sites)
- Mid-market: RON 2500–4000 (most SMEs end up here)
- Retainers: RON 1000–3000/month (recurring revenue opportunity)
- **For Seek Digital:** Position at "modern, affordable" if pricing 1500–2500 range; emphasize "transparent pricing" vs. competitors who hide it.

---

## 4. website_audit — Quality Audit (From URLs in Leads)

```json
[
  {
    "url": "https://casaveche-iasi.ro",
    "has_ssl": true,
    "has_viewport_meta": false,
    "copyright_year": 2019,
    "staleness_signal": "old",
    "cms_detected": "WordPress",
    "has_analytics": false,
    "mobile_score": 45,
    "performance_score": 38,
    "seo_score": 52,
    "audit_score": 4.5,
    "issues": [
      "No viewport meta tag — mobile users see broken layout",
      "7-year-old design — customers perceive as outdated",
      "No Google Analytics — can't measure ROI",
      "Slow load time (4.2s) — affects conversions",
      "Missing H1 tags — bad for SEO"
    ],
    "opportunities": [
      "Redesign with modern CMS or Webflow",
      "Install GA4 and conversion tracking",
      "Optimize images and enable caching"
    ],
    "source": "website_audit",
    "scraped_at": "2026-04-29T17:15:00Z"
  }
]
```

**Audit Score Scale:**
- 0–3: Critical issues (immediate modernization needed)
- 3–6: Poor (missing basics, lost opportunities)
- 6–8: Fair (functional but aging)
- 8–10: Good (modern, competitive)

**For Sales Pitch:** "Your site from 2019 gets outranked by competitors. Here's what we'll fix..." (then list issues above)

---

## Running These Locally

### With Zyte API key (production):
```bash
cd seek_digital_intelligence
export ZYTE_API_KEY="your_key_here"
./.venv/bin/scrapy crawl pagini_aurii -a industry=restaurante -a city=iasi -o leads.json
./.venv/bin/scrapy crawl facebook_ads -a industry=horeca -o ads.json
./.venv/bin/scrapy crawl competitor_pricing -o competitors.json
./.venv/bin/scrapy crawl website_audit -a urls=https://example.ro,https://example2.ro -o audits.json
```

### Local testing (no Zyte):
```bash
# Disable Zyte API and use standard requests:
./.venv/bin/scrapy crawl pagini_aurii \
  -a industry=restaurante \
  -a city=iasi \
  -a max_pages=1 \
  -s ZYTE_API_TRANSPARENT_MODE=False \
  -s DOWNLOAD_HANDLERS='' \
  -o leads.json
```

---

## Pipeline Flow

Each spider yields items → **LeadScoringPipeline** calculates `lead_score` + `lead_tier` → Output to CSV/JSON or **Airtable** (direct push)

**Example:**
1. pagini_aurii finds "Salon Elena" with no website
2. Pipeline scores: no_website (+25) + has_facebook (+5) + has_reviews (+10) = **lead_score 40** = **"warm"**
3. If facebook_ads finds her running ads (+30), score jumps to **70** = **"hot"**
4. Output to Airtable: auto-update `lead_tier` and flag for Tudor's first call

---
