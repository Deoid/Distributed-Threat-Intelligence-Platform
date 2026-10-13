import os

class Config:
    POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
    POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_DB = os.getenv("POSTGRES_DB", "threatintel")
    POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")

    DATABASE_URL = os.getenv(
        "DATABASE_URL",
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)
    REDIS_QUEUE_KEY = os.getenv("REDIS_QUEUE_KEY", "honeypot_events_queue")
    REDIS_CACHE_TTL = int(os.getenv("REDIS_CACHE_TTL", 60))  # 60 seconds default cache

    COLLECTOR_PORT = int(os.getenv("COLLECTOR_PORT", 5001))
    API_PORT = int(os.getenv("API_PORT", 5000))
    ENRICHER_BATCH_SIZE = int(os.getenv("ENRICHER_BATCH_SIZE", 50))
    ENRICHER_POLL_INTERVAL = float(os.getenv("ENRICHER_POLL_INTERVAL", 1.0))

    FALLBACK_SQLITE_PATH = os.getenv("FALLBACK_SQLITE_PATH", "threatintel.db")
