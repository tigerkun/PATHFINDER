from fastapi import APIRouter, Request

router = APIRouter(prefix="/api/v1", tags=["ops"])


@router.get("/live", summary="Liveness probe")
async def live():
    return {"status": "ok"}


@router.get("/ready", summary="Readiness probe")
async def ready(request: Request):
    return {"status": "ready", "request_id": getattr(request.state, "request_id", None)}
