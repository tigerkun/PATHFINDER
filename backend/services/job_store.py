import json
import sqlite3
import threading
import time
from typing import Any, Dict, Optional


class JobStore:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _connect(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    request_json TEXT NOT NULL,
                    result_json TEXT,
                    error_json TEXT
                )
                """
            )
            conn.commit()

    def upsert_job(self, job_id: str, status: str, request_data: Dict[str, Any], result: Optional[Dict[str, Any]] = None, error: Optional[Dict[str, Any]] = None):
        now = time.time()
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    INSERT INTO jobs (job_id, status, created_at, updated_at, request_json, result_json, error_json)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(job_id) DO UPDATE SET
                        status=excluded.status,
                        updated_at=excluded.updated_at,
                        request_json=excluded.request_json,
                        result_json=excluded.result_json,
                        error_json=excluded.error_json
                    """,
                    (
                        job_id,
                        status,
                        now,
                        now,
                        json.dumps(request_data),
                        json.dumps(result) if result is not None else None,
                        json.dumps(error) if error is not None else None,
                    ),
                )
                conn.commit()

    def touch_status(self, job_id: str, status: str, result: Optional[Dict[str, Any]] = None, error: Optional[Dict[str, Any]] = None):
        now = time.time()
        with self._lock:
            with self._connect() as conn:
                conn.execute(
                    """
                    UPDATE jobs
                    SET status = ?, updated_at = ?, result_json = COALESCE(?, result_json), error_json = COALESCE(?, error_json)
                    WHERE job_id = ?
                    """,
                    (
                        status,
                        now,
                        json.dumps(result) if result is not None else None,
                        json.dumps(error) if error is not None else None,
                        job_id,
                    ),
                )
                conn.commit()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT job_id, status, created_at, updated_at, request_json, result_json, error_json FROM jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        if not row:
            return None
        return {
            "job_id": row[0],
            "status": row[1],
            "created_at": row[2],
            "updated_at": row[3],
            "request": json.loads(row[4]) if row[4] else {},
            "result": json.loads(row[5]) if row[5] else None,
            "error": json.loads(row[6]) if row[6] else None,
        }

    def list_jobs(self, limit: int = 20, status: Optional[str] = None) -> list[Dict[str, Any]]:
        query = "SELECT job_id, status, created_at, updated_at, request_json, result_json, error_json FROM jobs"
        args: list[Any] = []
        if status:
            query += " WHERE status = ?"
            args.append(status)
        query += " ORDER BY created_at DESC LIMIT ?"
        args.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, tuple(args)).fetchall()
        return [
            {
                "job_id": row[0],
                "status": row[1],
                "created_at": row[2],
                "updated_at": row[3],
                "request": json.loads(row[4]) if row[4] else {},
                "result": json.loads(row[5]) if row[5] else None,
                "error": json.loads(row[6]) if row[6] else None,
            }
            for row in rows
        ]

    def delete_older_than(self, ttl_seconds: int):
        cutoff = time.time() - ttl_seconds
        with self._lock:
            with self._connect() as conn:
                conn.execute("DELETE FROM jobs WHERE updated_at < ?", (cutoff,))
                conn.commit()

