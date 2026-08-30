from services.github_service import GitHubService

from app.core.config import (
    DATA_BACKEND,
    JOB_DB_PATH,
    RATE_LIMIT_BACKEND,
    RATE_LIMIT_MAX_REQUESTS,
    RATE_LIMIT_REDIS_URL,
    RATE_LIMIT_WINDOW_SECONDS,
    SUPABASE_JOBS_TABLE,
    SUPABASE_PREDICTIONS_TABLE,
    SUPABASE_SERVICE_KEY,
    SUPABASE_URL,
)
from app.core.rate_limiter import MemoryRateLimiter, RedisRateLimiter
from app.repositories.inmemory_prediction_repository import InMemoryPredictionRepository
from app.repositories.sqlite_job_repository import SQLiteJobRepository
from app.repositories.supabase_job_repository import SupabaseJobRepository
from app.repositories.supabase_prediction_repository import SupabasePredictionRepository
from app.services.ai_provider import GeminiAIProvider
from app.services.job_application_service import JobApplicationService

gh_engine = GitHubService()
ai_engine = None
rate_limit_store = {}
runtime_metrics = {
    "requests_total": 0,
    "requests_by_status": {},
    "requests_by_path": {},
    "latency_ms_total": 0.0,
    "usage_daily": {},
}
rate_limiter = None

if DATA_BACKEND == "supabase":
    job_repository = SupabaseJobRepository(
        supabase_url=SUPABASE_URL,
        supabase_service_key=SUPABASE_SERVICE_KEY,
        table_name=SUPABASE_JOBS_TABLE,
    )
    prediction_repository = SupabasePredictionRepository(
        supabase_url=SUPABASE_URL,
        supabase_service_key=SUPABASE_SERVICE_KEY,
        table_name=SUPABASE_PREDICTIONS_TABLE,
    )
else:
    job_repository = SQLiteJobRepository(db_path=JOB_DB_PATH)
    prediction_repository = InMemoryPredictionRepository()

job_service = JobApplicationService(job_repository=job_repository, prediction_repository=prediction_repository)


def get_ai_engine():
    global ai_engine
    if ai_engine is None:
        ai_engine = GeminiAIProvider()
    return ai_engine


def get_rate_limiter():
    global rate_limiter
    if rate_limiter is not None:
        return rate_limiter
    if RATE_LIMIT_BACKEND == "redis":
        rate_limiter = RedisRateLimiter(
            redis_url=RATE_LIMIT_REDIS_URL,
            window_seconds=RATE_LIMIT_WINDOW_SECONDS,
            max_requests=RATE_LIMIT_MAX_REQUESTS,
        )
        return rate_limiter
    rate_limiter = MemoryRateLimiter(
        window_seconds=RATE_LIMIT_WINDOW_SECONDS,
        max_requests=RATE_LIMIT_MAX_REQUESTS,
        store=rate_limit_store,
    )
    return rate_limiter
