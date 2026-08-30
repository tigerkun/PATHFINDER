import hmac

from fastapi import Request
try:
    import jwt  # type: ignore
    from jwt import InvalidTokenError  # type: ignore
except ImportError:  # pragma: no cover - optional at runtime
    jwt = None
    class InvalidTokenError(Exception):
        pass

from app.core.config import (
    AUTH_MODE,
    API_AUTH_KEY,
    API_AUTH_MIN_LENGTH,
    JWT_ALGORITHM,
    JWT_AUDIENCE,
    JWT_ISSUER,
    JWT_SECRET_KEY,
    TRUST_PROXY_HEADERS,
)
from app.core.errors import api_error
from app.core.state import get_rate_limiter


def require_api_key(request: Request):
    if AUTH_MODE == "jwt":
        return _require_jwt(request)
    if AUTH_MODE == "api_key":
        return _require_api_key(request)
    jwt_result = _require_jwt(request)
    if jwt_result is None:
        return None
    return _require_api_key(request)


def _require_api_key(request: Request):
    provided = _extract_api_key(request)
    if _api_key_misconfigured():
        return api_error(
            request,
            500,
            "SERVER_MISCONFIGURED",
            f"API auth key is too short. Minimum length is {API_AUTH_MIN_LENGTH}.",
        )
    if not hmac.compare_digest(provided, API_AUTH_KEY):
        return api_error(request, 401, "UNAUTHORIZED", "Missing or invalid API key.")
    return None


def _extract_api_key(request: Request) -> str:
    header_key = request.headers.get("x-api-key", "").strip()
    if header_key:
        return header_key
    if request.url.path.endswith("/events"):
        return request.query_params.get("api_key", "").strip()
    return ""


def _api_key_misconfigured() -> bool:
    return len(API_AUTH_KEY) < API_AUTH_MIN_LENGTH


def _require_jwt(request: Request):
    token = _extract_bearer_token(request)
    if not token:
        return api_error(request, 401, "UNAUTHORIZED", "Missing bearer token.")
    if not JWT_SECRET_KEY:
        return api_error(request, 500, "SERVER_MISCONFIGURED", "JWT secret key is not configured.")
    if jwt is None:
        return api_error(request, 500, "SERVER_MISCONFIGURED", "JWT library is not installed.")
    try:
        payload = _decode_jwt_token(token)
    except (InvalidTokenError, ValueError, TypeError):
        return api_error(request, 401, "UNAUTHORIZED", "Invalid or expired JWT token.")
    request.state.auth_subject = payload.get("sub")
    return None


def _extract_bearer_token(request: Request) -> str:
    auth_header = request.headers.get("authorization", "").strip()
    if not auth_header.lower().startswith("bearer "):
        return ""
    return auth_header[7:].strip()


def _decode_jwt_token(token: str) -> dict:
    options = {"require": ["exp", "sub"]}
    kwargs = {"algorithms": [JWT_ALGORITHM], "options": options}
    if JWT_ISSUER:
        kwargs["issuer"] = JWT_ISSUER
    if JWT_AUDIENCE:
        kwargs["audience"] = JWT_AUDIENCE
    return jwt.decode(token, JWT_SECRET_KEY, **kwargs)


def get_client_ip(request: Request) -> str:
    if TRUST_PROXY_HEADERS:
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
    if request.client and request.client.host:
        return request.client.host
    return "unknown"


def check_rate_limit(client_ip: str) -> tuple[bool, int, int]:
    limiter = get_rate_limiter()
    result = limiter.check(client_ip)
    return result.allowed, result.remaining, result.retry_after
