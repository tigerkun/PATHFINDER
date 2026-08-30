from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


TERMINAL_JOB_STATUSES = {"completed", "failed", "cancelled"}


@dataclass
class JobRecord:
    job_id: str
    status: str
    created_at: float
    updated_at: float
    request: dict[str, Any]
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    attempts: int = 0

    def as_response(self) -> dict[str, Any]:
        payload = {
            "job_id": self.job_id,
            "job_status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }
        if self.status == "completed":
            payload["result"] = self.result
        if self.status in {"failed", "cancelled"}:
            payload["error"] = self.error
        return payload


class JobRepository(Protocol):
    def upsert_job(self, job: JobRecord) -> None: ...

    def get_job(self, job_id: str) -> JobRecord | None: ...

    def list_jobs(self, limit: int = 20, status: str | None = None) -> list[JobRecord]: ...

    def delete_older_than(self, ttl_seconds: int) -> None: ...
