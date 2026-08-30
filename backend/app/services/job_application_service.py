from __future__ import annotations

import asyncio
import json
import time
import uuid
from collections.abc import Awaitable, Callable
from typing import Any

from fastapi.responses import JSONResponse

from app.repositories.job_repository import JobRecord, TERMINAL_JOB_STATUSES
from app.repositories.prediction_repository import PredictionRecord


RunPredictionFn = Callable[..., Awaitable[dict[str, Any] | JSONResponse]]


class JobApplicationService:
    def __init__(self, job_repository, prediction_repository):
        self.job_repository = job_repository
        self.prediction_repository = prediction_repository
        self._tasks: dict[str, asyncio.Task] = {}

    def list_jobs(self, limit: int = 20, status: str | None = None) -> list[JobRecord]:
        return self.job_repository.list_jobs(limit=limit, status=status)

    def get_job(self, job_id: str) -> JobRecord | None:
        return self.job_repository.get_job(job_id)

    def create_job(self, request_payload: dict[str, Any]) -> JobRecord:
        now = time.time()
        job = JobRecord(
            job_id=str(uuid.uuid4()),
            status="queued",
            created_at=now,
            updated_at=now,
            request=request_payload,
            result=None,
            error=None,
            attempts=0,
        )
        self.job_repository.upsert_job(job)
        return job

    def enqueue_prediction_job(self, job: JobRecord, run_prediction: RunPredictionFn) -> None:
        self._tasks[job.job_id] = asyncio.create_task(self._run_prediction_job(job.job_id, run_prediction))

    async def _run_prediction_job(self, job_id: str, run_prediction: RunPredictionFn):
        job = self.get_job(job_id)
        if not job:
            return
        job.status = "running"
        job.updated_at = time.time()
        job.attempts += 1
        self.job_repository.upsert_job(job)

        try:
            result = await run_prediction(
                username=job.request["username"],
                cgpa=job.request["cgpa"],
                tier=job.request["tier"],
                target=job.request["target"],
                status=job.request["status"],
            )
            if isinstance(result, JSONResponse):
                job.status = "failed"
                job.error = json.loads(result.body.decode("utf-8"))
            else:
                job.status = "completed"
                job.result = result
                self.prediction_repository.save_prediction(
                    PredictionRecord(
                        prediction_id=str(uuid.uuid4()),
                        username=job.request["username"],
                        created_at=time.time(),
                        request=job.request,
                        result=result.get("data", {}),
                        metrics=result.get("metrics", {}),
                        meta=result.get("meta", {}),
                    )
                )
        except asyncio.CancelledError:
            job.status = "cancelled"
            job.error = {
                "status": "error",
                "error": {
                    "code": "JOB_CANCELLED",
                    "message": "Prediction job cancelled by client.",
                    "request_id": None,
                    "details": {},
                },
            }
            raise
        except Exception:
            job.status = "failed"
            job.error = {
                "status": "error",
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "Job failed due to an internal server error.",
                    "request_id": None,
                    "details": {},
                },
            }
        finally:
            job.updated_at = time.time()
            self.job_repository.upsert_job(job)

    def cancel_job(self, job_id: str) -> JobRecord | None:
        job = self.get_job(job_id)
        if not job:
            return None
        if job.status in TERMINAL_JOB_STATUSES:
            return job
        task = self._tasks.get(job_id)
        if task and not task.done():
            task.cancel()
        job.status = "cancelled"
        job.updated_at = time.time()
        job.error = {
            "status": "error",
            "error": {
                "code": "JOB_CANCELLED",
                "message": "Prediction job cancelled by client.",
                "request_id": None,
                "details": {},
            },
        }
        self.job_repository.upsert_job(job)
        return job

    def retry_job(self, job_id: str, run_prediction: RunPredictionFn) -> JobRecord | None:
        job = self.get_job(job_id)
        if not job:
            return None
        if job.status not in {"failed", "cancelled"}:
            return job
        job.status = "queued"
        job.updated_at = time.time()
        job.error = None
        self.job_repository.upsert_job(job)
        self.enqueue_prediction_job(job, run_prediction)
        return job

    def cleanup_old_jobs(self, ttl_seconds: int):
        self.job_repository.delete_older_than(ttl_seconds)
