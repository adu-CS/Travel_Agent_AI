"""
Central place for environment/config loading.
In production, these env vars should come from your platform's secret
manager (AWS Secrets Manager, GCP Secret Manager, k8s Secrets, etc),
not from a committed .env file. load_dotenv() is a harmless no-op if
no .env file is present, so this works in both local and prod.
"""
import os
import certifi
from dotenv import load_dotenv

load_dotenv()

# SSL certs (some corporate/py environments need this pinned explicitly)
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise ValueError(f"{name} is missing. Set it in your environment or .env file.")
    return value


GROQ_API_KEY = _require("GROQ_API_KEY")
DATABASE_URL = _require("DATABASE_URL")

# App-level auth key for the FastAPI endpoints (required in prod)
APP_API_KEY = os.getenv("APP_API_KEY")

# S3 (or S3-compatible) storage for generated PDFs
PDF_BUCKET = os.getenv("PDF_BUCKET")  # required if PDF upload is enabled
PDF_URL_EXPIRY_SECONDS = int(os.getenv("PDF_URL_EXPIRY_SECONDS", "86400"))

# Local fallback dir, used only if PDF_BUCKET is not set (e.g. local dev)
LOCAL_PDF_DIR = os.getenv("LOCAL_PDF_DIR", "outputs")

# Tuning knobs
REACT_MAX_STEPS = int(os.getenv("REACT_MAX_STEPS", "4"))
REACT_TIME_BUDGET_SECONDS = int(os.getenv("REACT_TIME_BUDGET_SECONDS", "45"))
DB_POOL_MAX_SIZE = int(os.getenv("DB_POOL_MAX_SIZE", "20"))

ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development | production

# Comma-separated list of allowed frontend origins for CORS, e.g.
# "https://app.yourdomain.com,https://yourdomain.com"
# In development, defaults to allowing localhost dev servers.
_default_origins = "http://localhost:5173,http://127.0.0.1:5173"
FRONTEND_ORIGINS = [
    o.strip() for o in os.getenv("FRONTEND_ORIGINS", _default_origins).split(",") if o.strip()
]