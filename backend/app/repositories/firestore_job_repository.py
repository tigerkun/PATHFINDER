from __future__ import annotations

from app.repositories.job_repository import JobRecord

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:  # pragma: no cover - optional dependency
    firebase_admin = None
    credentials = None
    firestore = None


class FirestoreJobRepository:
    def __init__(self, project_id: str, credentials_path: str = ""):
        if firebase_admin is None or firestore is None:
            raise RuntimeError("firebase-admin package is required for Firestore job repository.")
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault() if not credentials_path else credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
        self._db = firestore.client()
        self._collection = self._db.collection("jobs")

    def upsert_job(self, job: JobRecord) -> None:
        self._collection.document(job.job_id).set(
            {
                "job_id": job.job_id,
                "status": job.status,
                "created_at": job.created_at,
                "updated_at": job.updated_at,
                "request": job.request,
                "result": job.result,
                "error": job.error,
                "attempts": job.attempts,
            },
            merge=True,
        )

    def get_job(self, job_id: str) -> JobRecord | None:
        snapshot = self._collection.document(job_id).get()
        if not snapshot.exists:
            return None
        data = snapshot.to_dict() or {}
        return JobRecord(
            job_id=data.get("job_id", job_id),
            status=data.get("status", "queued"),
            created_at=float(data.get("created_at", 0.0)),
            updated_at=float(data.get("updated_at", 0.0)),
            request=data.get("request", {}),
            result=data.get("result"),
            error=data.get("error"),
            attempts=int(data.get("attempts", 0)),
        )

    def list_jobs(self, limit: int = 20, status: str | None = None) -> list[JobRecord]:
        query = self._collection.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
        if status:
            query = query.where("status", "==", status)
        records: list[JobRecord] = []
        for doc in query.stream():
            data = doc.to_dict() or {}
            records.append(
                JobRecord(
                    job_id=data.get("job_id", doc.id),
                    status=data.get("status", "queued"),
                    created_at=float(data.get("created_at", 0.0)),
                    updated_at=float(data.get("updated_at", 0.0)),
                    request=data.get("request", {}),
                    result=data.get("result"),
                    error=data.get("error"),
                    attempts=int(data.get("attempts", 0)),
                )
            )
        return records

    def delete_older_than(self, ttl_seconds: int) -> None:
        # TTL cleanup should be configured via Firestore TTL policy in production.
        return None
