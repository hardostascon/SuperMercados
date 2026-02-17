BOT_NAME = 'scrappers'

SPIDER_MODULES = ['scrappers.precio_scrapers.spiders']
NEWSPIDER_MODULE = 'scrappers.precio_scrapers.spiders'

# Respetar robots.txt
ROBOTSTXT_OBEY = True

# Configuración de concurrencia
CONCURRENT_REQUESTS = 8
DOWNLOAD_DELAY = 2

# User Agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Playwright configuración
DOWNLOAD_HANDLERS = {
    "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
    "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
}

TWISTED_REACTOR = "twisted.internet.asyncioreactor.AsyncioSelectorReactor"

# Pipelines activos - SQL Server
ITEM_PIPELINES = {
    'scrapers.pipelines.DataCleaningPipeline': 100,
    'scrapers.pipelines.SQLServerPipeline': 300,
}

# AutoThrottle (ajuste automático de velocidad)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0

# Logging
LOG_LEVEL = 'INFO'

# Retry
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]