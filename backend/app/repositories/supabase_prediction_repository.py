from __future__ import annotations

from typing import Any

import httpx

from app.repositories.prediction_repository import PredictionRecord


class SupabasePredictionRepository:
    def __init__(self, supabase_url: str, supabase_service_key: str, table_name: str = "predictions"):
        if not supabase_url or not supabase_service_key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY are required for Supabase backend.")
        self._base_url = supabase_url.rstrip("/")
        self._table = table_name
        self._headers = {
            "apikey": supabase_service_key,
            "Authorization": f"Bearer {supabase_service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        }

    def _endpoint(self) -> str:
        return f"{self._base_url}/rest/v1/{self._table}"

    async def save_prediction(self, record: PredictionRecord) -> None:
        payload = {
            "prediction_id": record.prediction_id,
            "username": record.username,
            "created_at": record.created_at,
            "request": record.request,
            "result": record.result,
            "metrics": record.metrics,
            "meta": record.meta,
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(self._endpoint(), headers=self._headers, json=payload)
            response.raise_for_status()

    async def list_predictions(self, username: str | None = None, limit: int = 20) -> list[PredictionRecord]:
        params: dict[str, Any] = {"order": "created_at.desc", "limit": str(limit)}
        if username:
            params["username"] = f"eq.{username}"
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(self._endpoint(), headers=self._headers, params=params)
            response.raise_for_status()
        rows = response.json()
        return [
            PredictionRecord(
                prediction_id=row["prediction_id"],
                username=row["username"],
                created_at=float(row["created_at"]),
                request=row.get("request") or {},
                result=row.get("result") or {},
                metrics=row.get("metrics") or {},
                meta=row.get("meta") or {},
            )
            for row in rows
        ]
