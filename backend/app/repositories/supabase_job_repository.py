from __future__ import annotations

import time
from typing import Any

import httpx

from app.repositories.job_repository import JobRecord


class SupabaseJobRepository:
    def __init__(self, supabase_url: str, supabase_service_key: str, table_name: str = "jobs"):
        if not supabase_url or not supabase_service_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY are required for Supabase backend.")
        self._base_url = supabase_url.rstrip("/")
        self._table = table_name
        self._headers = {
            "apikey": supabase_service_key,
            "Authorization": f"Bearer {supabase_service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation,resolution=merge-duplicates",
        }

    def _endpoint(self) -> str:
        return f"{self._base_url}/rest/v1/{self._table}"

    def upsert_job(self, job: JobRecord) -> None:
        payload = {
            "job_id": job.job_id,
            "status": job.status,
            "created_at": job.created_at,
            "updated_at": job.updated_at,
            "request": job.request,
            "result": job.result,
            "error": job.error,
            "attempts": job.attempts,
        }
        with httpx.Client(timeout=10.0) as client:
            client.post(self._endpoint(), headers=self._headers, params={"on_conflict": "job_id"}, json=payload).raise_for_status()

    def get_job(self, job_id: str) -> JobRecord | None:
        params = {"job_id": f"eq.{job_id}", "limit": 1}
        with httpx.Client(timeout=10.0) as client:
            response = client.get(self._endpoint(), headers=self._headers, params=params)
            response.raise_for_status()
        rows = response.json()
        if not rows:
            return None
        return self._to_record(rows[0])

    def list_jobs(self, limit: int = 20, status: str | None = None) -> list[JobRecord]:
        params: dict[str, Any] = {"order": "created_at.desc", "limit": str(limit)}
        if status:
            params["status"] = f"eq.{status}"
        with httpx.Client(timeout=10.0) as client:
            response = client.get(self._endpoint(), headers=self._headers, params=params)
            response.raise_for_status()
        rows = response.json()
        return [self._to_record(item) for item in rows]

    def delete_older_than(self, ttl_seconds: int) -> None:
        cutoff = time.time() - ttl_seconds
        with httpx.Client(timeout=10.0) as client:
            response = client.delete(self._endpoint(), headers=self._headers, params={"updated_at": f"lt.{cutoff}"})
            response.raise_for_status()

    @staticmethod
    def _to_record(row: dict[str, Any]) -> JobRecord:
        return JobRecord(
            job_id=row["job_id"],
            status=row["status"],
            created_at=float(row["created_at"]),
            updated_at=float(row["updated_at"]),
            request=row.get("request") or {},
            result=row.get("result"),
            error=row.get("error"),
            attempts=int(row.get("attempts", 0)),
        )
