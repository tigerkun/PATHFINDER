from fastapi import Request
from fastapi.responses import JSONResponse

from services.api_models import ApiErrorResponse


def api_error(
    request: Request | None,
    status_code: int,
    code: str,
    message: str,
    details: dict | None = None,
    headers: dict | None = None,
):
    payload = ApiErrorResponse(
        error={
            "code": code,
            "message": message,
            "request_id": getattr(request.state, "request_id", None) if request else None,
            "details": details or {},
        }
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump(), headers=headers or {})
