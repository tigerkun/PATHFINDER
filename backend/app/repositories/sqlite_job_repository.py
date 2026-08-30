from __future__ import annotations

from app.repositories.job_repository import JobRecord
from services.job_store import JobStore


class SQLiteJobRepository:
    def __init__(self, db_path: str):
        self._store = JobStore(db_path)

    def upsert_job(self, job: JobRecord) -> None:
        self._store.upsert_job(
            job_id=job.job_id,
            status=job.status,
            request_data=job.request,
            result=job.result,
            error=job.error,
        )

    def get_job(self, job_id: str) -> JobRecord | None:
        stored = self._store.get_job(job_id)
        if not stored:
            return None
        return JobRecord(
            job_id=stored["job_id"],
            status=stored["status"],
            created_at=stored["created_at"],
            updated_at=stored["updated_at"],
            request=stored["request"],
            result=stored["result"],
            error=stored["error"],
        )

    def list_jobs(self, limit: int = 20, status: str | None = None) -> list[JobRecord]:
        jobs = self._store.list_jobs(limit=limit, status=status)
        return [
            JobRecord(
                job_id=item["job_id"],
                status=item["status"],
                created_at=item["created_at"],
                updated_at=item["updated_at"],
                request=item["request"],
                result=item["result"],
                error=item["error"],
            )
            for item in jobs
        ]

    def delete_older_than(self, ttl_seconds: int) -> None:
        self._store.delete_older_than(ttl_seconds)
