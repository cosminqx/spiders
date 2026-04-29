import os
from dotenv import load_dotenv

load_dotenv()

BOT_NAME = "seek_intelligence"
SPIDER_MODULES = ["seek_intelligence.spiders"]
NEWSPIDER_MODULE = "seek_intelligence.spiders"

# ── Zyte API ──────────────────────────────────────────────────────────────────
ZYTE_API_KEY = os.getenv("ZYTE_API_KEY", "")

# Route ALL requests through Zyte API (handles proxying, anti-bot, JS rendering)
DOWNLOAD_HANDLERS = {
    "http":  "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
    "https": "scrapy_zyte_api.ScrapyZyteAPIDownloadHandler",
}
DOWNLOADER_MIDDLEWARES = {
    "scrapy_zyte_api.ScrapyZyteAPIDownloaderMiddleware": 1000,
}
SPIDER_MIDDLEWARES = {
    "scrapy_zyte_api.ScrapyZyteAPISpiderMiddleware": 100,
}
TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Default Zyte API options — each spider can override per request
ZYTE_API_TRANSPARENT_MODE = True   # auto-upgrades requests to Zyte API
ZYTE_API_BROWSER_HEADERS  = True   # realistic browser headers by default

# ── Concurrency & politeness ──────────────────────────────────────────────────
CONCURRENT_REQUESTS              = 4   # conservative — keeps us under radar
CONCURRENT_REQUESTS_PER_DOMAIN   = 2
DOWNLOAD_DELAY                   = 2   # seconds between requests per domain
RANDOMIZE_DOWNLOAD_DELAY         = True
AUTOTHROTTLE_ENABLED             = True
AUTOTHROTTLE_START_DELAY         = 1
AUTOTHROTTLE_MAX_DELAY           = 10
AUTOTHROTTLE_TARGET_CONCURRENCY  = 2.0
AUTOTHROTTLE_DEBUG               = False

# ── Retry ─────────────────────────────────────────────────────────────────────
RETRY_ENABLED   = True
RETRY_TIMES     = 3
RETRY_HTTP_CODES = [429, 500, 502, 503, 504]

# ── Cache (useful for dev; disable in production runs) ────────────────────────
HTTPCACHE_ENABLED    = False   # set True locally for faster dev iteration
HTTPCACHE_EXPIRATION_SECS = 3600
HTTPCACHE_DIR        = ".scrapy/httpcache"

# ── Output ────────────────────────────────────────────────────────────────────
FEEDS = {
    "output/%(spider)s/%(time)s.jsonl": {
        "format":   "jsonlines",
        "encoding": "utf8",
        "store_empty": False,
        "overwrite": False,
    },
    "output/%(spider)s/latest.csv": {
        "format":   "csv",
        "encoding": "utf8",
        "store_empty": False,
        "overwrite": True,
    },
}
FEED_EXPORT_ENCODING = "utf-8"

# ── Item pipelines ────────────────────────────────────────────────────────────
ITEM_PIPELINES = {
    "seek_intelligence.processors.pipeline.ValidatePipeline": 100,
    "seek_intelligence.processors.pipeline.LeadScoringPipeline": 200,
    "seek_intelligence.processors.pipeline.DeduplicationPipeline": 300,
}

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL  = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"

# ── Misc ──────────────────────────────────────────────────────────────────────
ROBOTSTXT_OBEY      = False   # directories often block all bots; we use Zyte
REQUEST_FINGERPRINTER_IMPLEMENTATION = "2.7"
TELNETCONSOLE_ENABLED = False
