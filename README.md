# Seek Digital — Market Intelligence Spider Suite

Automated market intelligence system for Seek Digital SRL.
Four spiders, one shared pipeline, direct Airtable integration.

---

## What this does

| Spider | Target | Output |
|---|---|---|
| `pagini_aurii` | Pagini Aurii directory | Romanian SME leads with website presence scored |
| `facebook_ads` | Facebook Ad Library (public) | Businesses actively spending on ads in Romania |
| `competitor_pricing` | Romanian web agency sites | Pricing matrix + positioning intelligence |
| `website_audit` | URLs from above spiders | Deep audit: staleness, mobile, CMS, analytics |

Every `BusinessItem` gets a **lead score (0–100)** and a **tier** (hot / warm / cold)
computed automatically by the pipeline before export.

---

## Project structure

```
seek_digital_intelligence/
├── seek_intelligence/
│   ├── spiders/
│   │   ├── pagini_aurii.py       ← SME lead discovery
│   │   ├── facebook_ads.py       ← Ad spend signals
│   │   ├── competitor_pricing.py ← Competitor analysis
│   │   └── website_audit.py      ← Website quality audit
│   ├── processors/
│   │   └── pipeline.py           ← Validate → Score → Deduplicate
│   ├── exporters/
│   │   └── airtable_exporter.py  ← Optional: push to Airtable directly
│   ├── items.py                  ← All data shapes
│   └── settings.py               ← Zyte API + concurrency config
├── .env.example                  ← Copy to .env, fill secrets
├── deploy_to_zyte.sh             ← One-command deployment
├── requirements.txt
└── scrapy.cfg
```

---

## Setup (local development)

```bash
# 1. Clone / unzip the project
cd seek_digital_intelligence

# 2. Create virtualenv
python3 -m venv .venv
source .venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure secrets
cp .env.example .env
# Edit .env — add your ZYTE_API_KEY at minimum

# 5. Test one spider locally (small crawl)
scrapy crawl pagini_aurii \
  -a industry=restaurante \
  -a city=iasi \
  -a max_pages=2 \
  -o test_output.csv
```

---

## Deploy to Zyte Cloud

```bash
# Install Zyte's deployment CLI
pip install shub

# Authenticate (one time)
shub login

# Deploy everything
chmod +x deploy_to_zyte.sh
./deploy_to_zyte.sh
```

After deploying:
1. Go to **app.zyte.com → your project → Settings → Environment Variables**
2. Add `ZYTE_API_KEY` with your key value
3. (Optional) Add `AIRTABLE_API_KEY` + `AIRTABLE_BASE_ID` for direct push

---

## Scheduling on Zyte Cloud

Go to **Spiders → [spider name] → Schedule**. Recommended:

| Spider | Schedule | Arguments |
|---|---|---|
| `pagini_aurii` | Daily 02:00 EET | `industry=restaurante,saloane-infrumusetare,cabinete-medicale city=iasi,cluj-napoca,timisoara` |
| `facebook_ads` | Every 3 days 03:00 | `industry=horeca` |
| `competitor_pricing` | Weekly Sunday 04:00 | *(no args needed)* |
| `website_audit` | Triggered after `pagini_aurii` | *(auto-loads latest CSV)* |

To chain `website_audit` after `pagini_aurii`, use Zyte's **Periodic Jobs → webhooks**
or set up a Make.com automation that watches for new files in your S3/GCS output bucket.

---

## Spider reference

### `pagini_aurii`
```bash
scrapy crawl pagini_aurii \
  -a industry=restaurante,cafenele,saloane-infrumusetare \
  -a city=iasi,cluj-napoca \
  -a max_pages=20
```
**Arguments:**
- `industry` — comma-separated (default: all 10 industries in spider)
- `city` — comma-separated (default: all 13 cities in spider)
- `max_pages` — max pagination depth per industry+city combo (default: 20)

**Output fields:** name, industry, city, phone, website_url, has_website,
has_facebook, has_instagram, review_count, avg_rating, lead_score, lead_tier

---

### `facebook_ads`
```bash
scrapy crawl facebook_ads \
  -a industry=horeca \
  -a country=RO \
  -a max_pages=5
```
**Arguments:**
- `industry` — one of: horeca, beauty, medical, auto, fitness, retail, real_estate
- `query` — alternative: pass raw search terms (comma-separated)
- `country` — default RO

**Output fields:** advertiser_name, is_active, run_days, budget_signal,
estimated_spend, landing_url, industry_tag

**Budget signals:**
- `confirmed_spender` — active 60+ days (has budget, committed)
- `active` — active 14–59 days
- `testing` — under 14 days

---

### `competitor_pricing`
```bash
scrapy crawl competitor_pricing -a include_clutch=true
```
**Output fields:** agency_name, city, entry_price, mid_price, premium_price,
monthly_retainer, pricing_visible, services_offered, positioning_copy,
guarantee_mentioned

**Add more competitors:** Edit `COMPETITOR_SEEDS` list in `competitor_pricing.py`

---

### `website_audit`
```bash
# Audit specific URLs
scrapy crawl website_audit \
  -a urls=https://example.ro,https://example2.ro

# Audit everything from latest pagini_aurii run
scrapy crawl website_audit \
  -a input_file=output/pagini_aurii/latest.csv
```
**Output fields:** url, has_ssl, has_viewport_meta, copyright_year,
staleness_signal, cms_detected, has_analytics, audit_score (0–10, lower = worse)

---

## Lead scoring logic

Scoring runs automatically in `LeadScoringPipeline` on every `BusinessItem`:

| Signal | Points | What it means for Seek Digital |
|---|---|---|
| No website | +25 | Obvious gap — easiest pitch |
| Outdated site (5+ years) | +15 | Clear upgrade opportunity |
| Not mobile-optimised | +15 | Measurable problem we can cite |
| 20+ reviews | +10 | Active business with customers |
| Has social media | +5 | Already cares about digital |
| No analytics | +5 | Flying blind — we can fix that |
| Running ads* | +30 | Has budget, confirmed spender |

*Ad signal joined from `facebook_ads` output in Airtable via business name match.

**Tiers:**
- `hot` (50+) — Tudor calls these first, same day
- `warm` (25–49) — follow up within a week
- `cold` (<25) — batch outreach, lower personalisation

---

## Airtable integration

### Option A: CSV import (MVP, manual)
After each run, download `output/[spider]/latest.csv` from Zyte Cloud
and import to your Airtable base.

### Option B: Direct push (automated)
1. `pip install pyairtable` (already in requirements.txt)
2. Add Airtable credentials to `.env`
3. In `settings.py`, add to `ITEM_PIPELINES`:
   ```python
   "seek_intelligence.exporters.airtable_exporter.AirtablePipeline": 400,
   ```

### Airtable table structure

**Business Registry** table — fields to create:
`Name | Industry | City | Phone | Website | Has Website | Lead Score | Lead Tier | Review Count | Has Facebook | Status | Notes | Assigned To | Scraped At`

**Ad Signals** table:
`Advertiser | Is Active | Run Days | Budget Signal | Industry | Landing URL | Scraped At`

**Competitor Intelligence** table:
`Agency Name | URL | City | Entry Price | Mid Price | Premium Price | Monthly Retainer | Pricing Visible | Services | Positioning | Guarantee | Scraped At`

---

## Cross-referencing leads with ad data

The most powerful thing this system does is identify businesses that:
1. Are running Facebook ads (from `facebook_ads`) **AND**
2. Have a weak or missing website (from `pagini_aurii` + `website_audit`)

In Airtable, create a **formula field** or use **Make.com** to:
1. Match `facebook_ads.advertiser_name` → `business_registry.name` (fuzzy match)
2. When matched, add +30 to `lead_score` and flag as `running_ads = true`
3. Auto-update `lead_tier` to "hot"

These are your warmest leads — they have budget, they understand digital, they just have a gap you can fill.

---

## Extending the system

**Add a new competitor:** Edit `COMPETITOR_SEEDS` in `competitor_pricing.py`

**Add a new industry:** Add to `DEFAULT_INDUSTRIES` in `pagini_aurii.py`
and `INDUSTRY_QUERIES` in `facebook_ads.py`

**Add a new city:** Add to `DEFAULT_CITIES` in `pagini_aurii.py`

**Add a new data source** (e.g. listafirme.ro, ejobs.ro for hiring signals):
Create a new spider in `seek_intelligence/spiders/` following the same pattern.
Yield a `BusinessItem` and the scoring pipeline runs automatically.

---

## Cost estimates (Zyte Cloud)

| Spider | Pages/run | Estimated Zyte API cost |
|---|---|---|
| `pagini_aurii` (all cities × all industries) | ~2,600 | ~$8–15/run |
| `facebook_ads` (all industries) | ~500 | ~$5–8/run |
| `competitor_pricing` | ~200 | ~$2–4/run |
| `website_audit` (500 URLs) | ~500 | ~$3–6/run |

Monthly total (recommended schedules): **~$60–100/month**
At Zyte's Starter plan pricing. Scale down by narrowing industries/cities during MVP phase.

---

## Questions / issues

Owner: Silviu Chiscareanu (CEO & Technical Lead, Seek Digital SRL)
