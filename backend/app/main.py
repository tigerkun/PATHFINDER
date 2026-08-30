from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.core.config import (
    ALLOWED_HOSTS,
    APP_ENV,
    AUTH_MODE,
    API_AUTH_KEY,
    API_AUTH_MIN_LENGTH,
    API_VERSION,
    CONTENT_SECURITY_POLICY,
    CORS_ORIGINS,
    ENABLE_SECURITY_HEADERS,
    ENABLE_HTTPS_REDIRECT,
    JWT_SECRET_KEY,
    DATA_BACKEND,
    QUEUE_BACKEND,
    RATE_LIMIT_BACKEND,
    RATE_LIMIT_REDIS_URL,
    STATIC_DIR,
    SUPABASE_SERVICE_KEY,
    SUPABASE_URL,
    TEMPLATES_DIR,
)
from app.core.middleware import observability_middleware
from app.routers import analytics, meta, ops, prediction, web

if not API_AUTH_KEY:
    raise RuntimeError("API_AUTH_KEY must be set before starting the API.")
if len(API_AUTH_KEY) < API_AUTH_MIN_LENGTH:
    raise RuntimeError(
        f"API_AUTH_KEY must be at least {API_AUTH_MIN_LENGTH} characters long for secure deployments."
    )
if ENABLE_SECURITY_HEADERS and not CONTENT_SECURITY_POLICY.strip():
    raise RuntimeError("CONTENT_SECURITY_POLICY cannot be empty when ENABLE_SECURITY_HEADERS=true.")
if AUTH_MODE not in {"api_key", "jwt", "hybrid"}:
    raise RuntimeError("AUTH_MODE must be one of: api_key, jwt, hybrid.")
if AUTH_MODE in {"jwt", "hybrid"} and not JWT_SECRET_KEY:
    raise RuntimeError("JWT_SECRET_KEY must be set when AUTH_MODE is jwt or hybrid.")
if RATE_LIMIT_BACKEND not in {"memory", "redis"}:
    raise RuntimeError("RATE_LIMIT_BACKEND must be either memory or redis.")
if RATE_LIMIT_BACKEND == "redis" and not RATE_LIMIT_REDIS_URL:
    raise RuntimeError("RATE_LIMIT_REDIS_URL must be set when RATE_LIMIT_BACKEND=redis.")
if APP_ENV in {"production", "prod"} and RATE_LIMIT_BACKEND != "redis":
    raise RuntimeError("RATE_LIMIT_BACKEND must be redis in production.")
if DATA_BACKEND not in {"sqlite", "supabase"}:
    raise RuntimeError("DATA_BACKEND must be either sqlite or supabase.")
if DATA_BACKEND == "supabase" and (not SUPABASE_URL or not SUPABASE_SERVICE_KEY):
    raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set when DATA_BACKEND=supabase.")
if QUEUE_BACKEND not in {"inprocess"}:
    raise RuntimeError("QUEUE_BACKEND currently supports: inprocess")

app = FastAPI(
    title="Career Intelligence Engine",
    description="Backend APIs for GitHub-driven career intelligence.",
    version=API_VERSION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key"],
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)
if ENABLE_HTTPS_REDIRECT:
    app.add_middleware(HTTPSRedirectMiddleware)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
app.state.templates = Jinja2Templates(directory=str(TEMPLATES_DIR))
app.middleware("http")(observability_middleware)
app.include_router(web.router)
app.include_router(prediction.router)
app.include_router(meta.router)
app.include_router(analytics.router)
app.include_router(ops.router)
