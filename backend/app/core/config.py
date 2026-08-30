import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

API_VERSION = "2.3.0"

BASE_DIR = Path(__file__).resolve().parent.parent.parent
STATIC_DIR = BASE_DIR / "static"
TEMPLATES_DIR = BASE_DIR / "templates"

API_AUTH_KEY = os.getenv("API_AUTH_KEY", "").strip()
API_AUTH_MIN_LENGTH = int(os.getenv("API_AUTH_MIN_LENGTH", "16"))
AUTH_MODE = os.getenv("AUTH_MODE", "hybrid").strip().lower()
APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "").strip()
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256").strip()
JWT_ISSUER = os.getenv("JWT_ISSUER", "").strip()
JWT_AUDIENCE = os.getenv("JWT_AUDIENCE", "").strip()
CORS_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000").split(",")
    if origin.strip()
]
TRUST_PROXY_HEADERS = os.getenv("TRUST_PROXY_HEADERS", "false").lower() == "true"
ENABLE_HTTPS_REDIRECT = os.getenv("ENABLE_HTTPS_REDIRECT", "false").lower() == "true"
ENABLE_SECURITY_HEADERS = os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true"
ALLOWED_HOSTS = [h.strip() for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(",") if h.strip()]
CONTENT_SECURITY_POLICY = os.getenv(
    "CONTENT_SECURITY_POLICY",
    "default-src 'self'; img-src 'self' data:; script-src 'self'; style-src 'self' https://fonts.googleapis.com; font-src 'self' https://fonts.gstatic.com; connect-src 'self'; frame-ancestors 'none'",
)

RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_MAX_REQUESTS = int(os.getenv("RATE_LIMIT_MAX_REQUESTS", "15"))
RATE_LIMIT_BACKEND = os.getenv("RATE_LIMIT_BACKEND", "memory").strip().lower()
RATE_LIMIT_REDIS_URL = os.getenv("RATE_LIMIT_REDIS_URL", "redis://localhost:6379/0").strip()
JOB_TTL_SECONDS = int(os.getenv("JOB_TTL_SECONDS", "3600"))
JOB_DB_PATH = os.getenv("JOB_DB_PATH", str(BASE_DIR / "jobs.db"))
DATA_BACKEND = os.getenv("DATA_BACKEND", "sqlite").strip().lower()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "").strip()
SUPABASE_JOBS_TABLE = os.getenv("SUPABASE_JOBS_TABLE", "jobs").strip()
SUPABASE_PREDICTIONS_TABLE = os.getenv("SUPABASE_PREDICTIONS_TABLE", "predictions").strip()
QUEUE_BACKEND = os.getenv("QUEUE_BACKEND", "inprocess").strip().lower()

TIERS = ("tier1", "tier2", "tier3")
TARGETS = (
    "software_engineer",
    "backend_engineer",
    "frontend_engineer",
    "fullstack_engineer",
    "ml_engineer",
    "data_engineer",
    "devops_engineer",
    "mobile_engineer",
    "security_engineer",
)
STATUSES = ("student", "fresher", "experienced", "senior")
DEFAULTS = {"cgpa": 7.0, "tier": "tier2", "target": "software_engineer", "status": "student"}
