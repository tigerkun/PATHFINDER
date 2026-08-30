from fastapi import APIRouter, Request

from app.core.security import require_api_key
from app.core.state import prediction_repository, runtime_metrics

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])


@router.get("/usage", summary="Usage analytics snapshot")
async def usage(request: Request, username: str | None = None, limit: int = 20):
    unauthorized = require_api_key(request)
    if unauthorized:
        return unauthorized
    records = prediction_repository.list_predictions(username=username, limit=max(1, min(limit, 100)))
    return {
        "status": "success",
        "data": {
            "count": len(records),
            "daily": runtime_metrics["usage_daily"],
            "items": [
                {
                    "prediction_id": item.prediction_id,
                    "username": item.username,
                    "created_at": item.created_at,
                    "meta": item.meta,
                }
                for item in records
            ],
        },
    }


@router.get("/latency", summary="Latency analytics snapshot")
async def latency(request: Request):
    unauthorized = require_api_key(request)
    if unauthorized:
        return unauthorized
    total = runtime_metrics["requests_total"]
    average_ms = (runtime_metrics["latency_ms_total"] / total) if total else 0.0
    return {
        "status": "success",
        "data": {
            "requests_total": total,
            "average_latency_ms": round(average_ms, 2),
        },
    }
