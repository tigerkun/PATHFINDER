import time
import uuid
import logging
import secrets
from datetime import datetime, timezone

from app.core.config import CONTENT_SECURITY_POLICY, ENABLE_SECURITY_HEADERS
from app.core.state import runtime_metrics

logger = logging.getLogger("pathfinder.api")


async def observability_middleware(request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    request.state.csp_nonce = secrets.token_urlsafe(16)
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    path = request.url.path
    status_code = response.status_code

    runtime_metrics["requests_total"] += 1
    runtime_metrics["latency_ms_total"] += elapsed_ms
    runtime_metrics["requests_by_status"][status_code] = runtime_metrics["requests_by_status"].get(status_code, 0) + 1
    runtime_metrics["requests_by_path"][path] = runtime_metrics["requests_by_path"].get(path, 0) + 1
    usage_day = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    day_stats = runtime_metrics["usage_daily"].setdefault(usage_day, {"requests": 0, "paths": {}})
    day_stats["requests"] += 1
    day_stats["paths"][path] = day_stats["paths"].get(path, 0) + 1

    logger.info(
        "request_complete request_id=%s method=%s path=%s status=%s latency_ms=%.2f",
        request_id,
        request.method,
        path,
        status_code,
        elapsed_ms,
    )
    if ENABLE_SECURITY_HEADERS:
        csp_value = CONTENT_SECURITY_POLICY
        nonce = getattr(request.state, "csp_nonce", "")
        if nonce and "style-src" in csp_value and "'nonce-" not in csp_value:
            csp_value = csp_value.replace("style-src 'self'", f"style-src 'self' 'nonce-{nonce}'")
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        response.headers["Content-Security-Policy"] = csp_value
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time-ms"] = f"{elapsed_ms:.2f}"
    return response
