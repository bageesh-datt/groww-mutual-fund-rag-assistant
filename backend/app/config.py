import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_file = BASE_DIR / "backend" / ".env"
if env_file.exists():
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k, v)

class Settings:
    # App Information
    PROJECT_NAME: str = "Groww Mutual Fund Facts-Only FAQ Assistant"
    VERSION: str = "1.0.0"
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Ingestion Scope: Strictly 5 Groww URLs
    ALLOWED_URLS: list[str] = [
        "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",
        "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
        "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    ]

    # Map of scheme slugs to details
    SCHEME_URL_MAP: dict[str, dict[str, str]] = {
        "hdfc-mid-cap-fund-direct-growth": {
            "scheme_name": "HDFC Mid-Cap Opportunities Fund Direct Growth",
            "url": "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
            "category": "Mid Cap Equity"
        },
        "hdfc-silver-etf-fof-direct-growth": {
            "scheme_name": "HDFC Silver ETF Fund of Fund Direct Growth",
            "url": "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",
            "category": "Commodity / Silver FoF"
        },
        "hdfc-defence-fund-direct-growth": {
            "scheme_name": "HDFC Defence Fund Direct Growth",
            "url": "https://groww.in/mutual-funds/hdfc-defence-fund-direct-growth",
            "category": "Thematic Equity / Defence"
        },
        "hdfc-equity-fund-direct-growth": {
            "scheme_name": "HDFC Flexi Cap Fund Direct Growth",
            "url": "https://groww.in/mutual-funds/hdfc-equity-fund-direct-growth",
            "category": "Flexi Cap Equity"
        },
        "hdfc-small-cap-fund-direct-growth": {
            "scheme_name": "HDFC Small Cap Fund Direct Growth",
            "url": "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
            "category": "Small Cap Equity"
        }
    }

    # Data Storage Paths
    RAW_DATA_DIR: Path = BASE_DIR / "data" / "raw"
    PROCESSED_DATA_DIR: Path = BASE_DIR / "data" / "processed"
    VECTOR_DB_DIR: Path = BASE_DIR / "data" / "vector_db"

    # Automated Scheduler Configuration (Daily at 9:15 AM IST)
    INGESTION_CRON_SCHEDULE: str = os.getenv("INGESTION_CRON_SCHEDULE", "15 9 * * *")
    SCHEDULE_HOUR: int = int(os.getenv("SCHEDULE_HOUR", "9"))
    SCHEDULE_MINUTE: int = int(os.getenv("SCHEDULE_MINUTE", "15"))

    # Embedding & Vector Database Settings
    EMBEDDING_MODEL_NAME: str = os.getenv("EMBEDDING_MODEL_NAME", "BAAI/bge-large-en-v1.5")
    EMBEDDING_DIMENSION: int = int(os.getenv("EMBEDDING_DIMENSION", "1024"))
    CHROMA_COLLECTION_NAME: str = os.getenv("CHROMA_COLLECTION_NAME", "groww_mf_chunks")

    # RAG Retrieval & Guardrail Parameters
    CONFIDENCE_THRESHOLD: float = float(os.getenv("CONFIDENCE_THRESHOLD", "0.75"))
    MAX_SENTENCES_LIMIT: int = int(os.getenv("MAX_SENTENCES_LIMIT", "3"))
    REQUIRED_CITATION_COUNT: int = int(os.getenv("REQUIRED_CITATION_COUNT", "1"))
    
    # Standard System Texts
    DISCLAIMER_TEXT: str = "Facts-only. No investment advice."
    FALLBACK_RESPONSE_TEXT: str = "I couldn't verify this information from the available official sources."
    ADVISORY_REFUSAL_TEXT: str = (
        "I can provide factual information about supported mutual fund schemes, but I cannot offer "
        "investment advice, opinions, or fund recommendations. You can review the official scheme page for objective details."
    )

    # API Keys
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", os.getenv("OPENAI_API_KEY", ""))
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", os.getenv("GROQ_API_KEY", ""))

settings = Settings()
