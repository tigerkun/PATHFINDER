from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class PredictionRecord:
    prediction_id: str
    username: str
    created_at: float
    request: dict[str, Any]
    result: dict[str, Any]
    metrics: dict[str, Any]
    meta: dict[str, Any]


class PredictionRepository(Protocol):
    async def save_prediction(self, record: PredictionRecord) -> None: ...

    async def list_predictions(self, username: str | None = None, limit: int = 20) -> list[PredictionRecord]: ...
