import asyncio
import json
import time
import uuid

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

from app.core.jobs import cleanup_old_jobs, persist_job, snapshot_job, start_prediction_job
from app.core.security import check_rate_limit, get_client_ip, require_api_key
from app.core.state import job_service, prediction_repository
from app.repositories.prediction_repository import PredictionRecord
from app.domain.prediction import run_prediction, run_profile_metrics
from app.core.errors import api_error
from services.api_models import ApiErrorResponse, JobCreateResponse, JobStatusResponse, PredictRequest, PredictSuccessResponse, ProfileResponse

router = APIRouter(prefix="/api/v1", tags=["prediction"])

ERROR_RESPONSES = {
    400: {"model": ApiErrorResponse, "description": "Bad request"},
    401: {"model": ApiErrorResponse, "description": "Missing or invalid API key"},
    404: {"model": ApiErrorResponse, "description": "Resource not found"},
    429: {"model": ApiErrorResponse, "description": "Rate limit exceeded"},
    500: {"model": ApiErrorResponse, "description": "Internal server error"},
}


@router.post(
    "/predict",
    summary="Synchronous prediction via JSON body",
    response_model=PredictSuccessResponse,
    responses=ERROR_RESPONSES,
)
async def predict_post(request: Request, payload: PredictRequest):
    unauthorized = require_api_key(request)
    if unauthorized:
        return unauthorized
    client_ip = get_client_ip(request)
    allowed, remaining, retry_after = check_rate_limit(client_ip)
    if not allowed:
        return api_error(
            request,
            429,
            "RATE_LIMIT_EXCEEDED",
            "Rate limit exceeded. Please retry later.",
            {"retry_after_seconds": retry_after},
            headers={"Retry-After": str(retry_after), "X-RateLimit-Remaining": "0"},
        )
    result_data = await run_prediction(
        username=payload.username,
        cgpa=payload.cgpa,
        tier=payload.tier,
        target=payload.target,
        status=payload.status,
    )
    if isinstance(result_data, JSONResponse):
        result_data.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        return result_data
    prediction_repository.save_prediction(
        PredictionRecord(
            prediction_id=str(uuid.uuid4()),
            username=result_data["request"]["username"],
            created_at=time.time(),
            request=result_data["request"],
            result=result_data["data"],
            metrics=result_data["metrics"],
            meta=result_data["meta"],
        )
    )
    response = JSONResponse(content=result_data)
    response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
    return response


@router.get(
    "/profile/{username}",
    tags=["profile"],
    summary="Get fast GitHub metrics only",
    response_model=ProfileResponse,
    responses=ERROR_RESPONSES,
)
async def profile(request: Request, username: str):
    unauthorized = require_api_key(request)
    if unauthorized:
        return unauthorized
    return await run_profile_metrics(username)


@router.post(
    "/predict/jobs",
    summary="Create async prediction job",
    response_model=JobCreateResponse,
    responses=ERROR_RESPONSES,
)
async def create_predict_job(request: Request, payload: PredictRequest):
    unauthorized = require_api_key(request)
    if unauthorized:
        return unauthorized
    client_ip = get_client_ip(request)
    allowed, _, retry_after = check_rate_limit(client_ip)
    if not allowed:
        return api_error(
            request,
            429,
            "RATE_LIMIT_EXCEEDED",
            "Rate limit exceeded. Please retry later.",
            {"retry_after_seconds": retry_after},
            headers={"Retry-After": str(retry_after)},
        )

    cleanup_old_jobs()
    job = job_service.create_job(payload.model_dump())
    persist_job(job.job_id)
    start_prediction_job(job.job_id, payload, run_prediction)
    return {"status": "accepted", "job_id": job.job_id, "poll_url": f"/api/v1/predict/jobs/{job.job_id}"}


@router.get(
    "/predict/jobs",
    summary="List async prediction jobs",
    responses=ERROR_RESPONSES,
)
async def list_predict_jobs(request: Request, status: str | None = None, limit: int = 20):
    unauthorized = require_api_key(request)
    if unauthorized:
        return unauthorized
    items = job_service.list_jobs(limit=max(1, min(limit, 100)), status=status)
    return {"status": "success", "data": {"items": [item.as_response() for item in items]}}


@router.get(
    "/predict/jobs/{job_id}",
    summary="Get async prediction job status",
    response_model=JobStatusResponse,
    responses=ERROR_RESPONSES,
)
async def get_predict_job(request: Request, job_id: str):
    unauthorized = require_api_key(request)
    if unauthorized:
        return unauthorized
    cleanup_old_jobs()
    job = snapshot_job(job_id)
    if not job:
        return api_error(request, 404, "JOB_NOT_FOUND", "Job not found")

    response = {
        "status": "success",
        "data": {
            "job_id": job_id,
            "job_status": job["status"],
            "created_at": job["created_at"],
            "updated_at": job["updated_at"],
        },
    }
    if job["status"] == "completed":
        response["data"]["result"] = job["result"]
    if job["status"] in ("failed", "cancelled"):
        response["data"]["error"] = job["error"]
    return response


@router.delete(
    "/predict/jobs/{job_id}",
    summary="Cancel async prediction job",
    responses=ERROR_RESPONSES,
)
async def cancel_predict_job(request: Request, job_id: str):
    unauthorized = require_api_key(request)
    if unauthorized:
        return unauthorized
    cleanup_old_jobs()
    job = job_service.get_job(job_id)
    if not job:
        persisted = snapshot_job(job_id)
        if persisted and persisted["status"] in ("completed", "failed", "cancelled"):
            return {
                "status": "success",
                "data": {"job_id": job_id, "job_status": persisted["status"], "message": "Job is already terminal."},
            }
        return api_error(request, 404, "JOB_NOT_FOUND", "Job not found")

    if job.status in ("completed", "failed", "cancelled"):
        return {
            "status": "success",
            "data": {"job_id": job_id, "job_status": job.status, "message": "Job is already terminal."},
        }
    cancelled = job_service.cancel_job(job_id)
    if not cancelled:
        return api_error(request, 404, "JOB_NOT_FOUND", "Job not found")
    persist_job(job_id)
    return {"status": "success", "data": {"job_id": job_id, "job_status": cancelled.status}}


@router.post(
    "/predict/jobs/{job_id}/retry",
    summary="Retry failed or cancelled async prediction job",
    responses=ERROR_RESPONSES,
)
async def retry_predict_job(request: Request, job_id: str):
    unauthorized = require_api_key(request)
    if unauthorized:
        return unauthorized
    retried = job_service.retry_job(job_id, run_prediction=run_prediction)
    if not retried:
        return api_error(request, 404, "JOB_NOT_FOUND", "Job not found")
    return {"status": "success", "data": {"job_id": job_id, "job_status": retried.status}}


@router.get(
    "/predict/jobs/{job_id}/events",
    summary="SSE stream for async job updates",
    responses=ERROR_RESPONSES,
)
async def stream_predict_job_events(request: Request, job_id: str):
    unauthorized = require_api_key(request)
    if unauthorized:
        return unauthorized

    queue: asyncio.Queue = asyncio.Queue()

    async def event_generator():
        try:
            while True:
                job = snapshot_job(job_id)
                if not job:
                    yield "event: error\ndata: {\"code\":\"JOB_NOT_FOUND\",\"message\":\"Job not found\"}\n\n"
                    break

                payload = {"job_id": job_id, "job_status": job["status"], "updated_at": job["updated_at"]}
                if job["status"] == "completed":
                    payload["result"] = job["result"]
                if job["status"] in ("failed", "cancelled"):
                    payload["error"] = job["error"]
                yield f"event: status\ndata: {json.dumps(payload)}\n\n"

                if job["status"] in ("completed", "failed", "cancelled"):
                    break
                await asyncio.sleep(1.5)
        finally:
            while not queue.empty():
                queue.get_nowait()

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@router.get(
    "/predict/{username}",
    summary="Synchronous prediction via URL params",
    response_model=PredictSuccessResponse,
    responses=ERROR_RESPONSES,
)
async def predict(
    request: Request,
    username: str,
    cgpa: float = 7.0,
    tier: str = "tier2",
    target: str = "software_engineer",
    status: str = "student",
):
    unauthorized = require_api_key(request)
    if unauthorized:
        return unauthorized
    client_ip = get_client_ip(request)
    allowed, remaining, retry_after = check_rate_limit(client_ip)
    if not allowed:
        return api_error(
            request,
            429,
            "RATE_LIMIT_EXCEEDED",
            "Rate limit exceeded. Please retry later.",
            {"retry_after_seconds": retry_after},
            headers={"Retry-After": str(retry_after), "X-RateLimit-Remaining": "0"},
        )
    result_data = await run_prediction(username, cgpa, tier, target, status)
    if isinstance(result_data, JSONResponse):
        result_data.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        return result_data
    prediction_repository.save_prediction(
        PredictionRecord(
            prediction_id=str(uuid.uuid4()),
            username=result_data["request"]["username"],
            created_at=time.time(),
            request=result_data["request"],
            result=result_data["data"],
            metrics=result_data["metrics"],
            meta=result_data["meta"],
        )
    )
    response = JSONResponse(content=result_data)
    response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
    return response


@router.get(
    "/predictions/history",
    summary="Prediction history with pagination",
    responses=ERROR_RESPONSES,
)
async def prediction_history(request: Request, username: str | None = None, limit: int = 20):
    unauthorized = require_api_key(request)
    if unauthorized:
        return unauthorized
    items = prediction_repository.list_predictions(username=username, limit=max(1, min(limit, 100)))
    return {
        "status": "success",
        "data": {
            "items": [
                {
                    "prediction_id": item.prediction_id,
                    "username": item.username,
                    "created_at": item.created_at,
                    "request": item.request,
                    "result": item.result,
                    "metrics": item.metrics,
                    "meta": item.meta,
                }
                for item in items
            ]
        },
    }
