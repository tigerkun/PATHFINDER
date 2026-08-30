from __future__ import annotations

from app.repositories.prediction_repository import PredictionRecord


class InMemoryPredictionRepository:
    def __init__(self):
        self._items: list[PredictionRecord] = []

    def save_prediction(self, record: PredictionRecord) -> None:
        self._items.insert(0, record)

    def list_predictions(self, username: str | None = None, limit: int = 20) -> list[PredictionRecord]:
        records = self._items
        if username:
            records = [item for item in records if item.username.lower() == username.lower()]
        return records[:limit]
