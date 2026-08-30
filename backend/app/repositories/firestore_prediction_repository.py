from __future__ import annotations

from app.repositories.prediction_repository import PredictionRecord

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:  # pragma: no cover - optional dependency
    firebase_admin = None
    credentials = None
    firestore = None


class FirestorePredictionRepository:
    def __init__(self, project_id: str, credentials_path: str = ""):
        if firebase_admin is None or firestore is None:
            raise RuntimeError("firebase-admin package is required for Firestore prediction repository.")
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault() if not credentials_path else credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
        self._collection = firestore.client().collection("predictions")

    def save_prediction(self, record: PredictionRecord) -> None:
        self._collection.document(record.prediction_id).set(
            {
                "prediction_id": record.prediction_id,
                "username": record.username,
                "created_at": record.created_at,
                "request": record.request,
                "result": record.result,
                "metrics": record.metrics,
                "meta": record.meta,
            }
        )

    def list_predictions(self, username: str | None = None, limit: int = 20) -> list[PredictionRecord]:
        query = self._collection.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
        if username:
            query = query.where("username", "==", username)
        records: list[PredictionRecord] = []
        for doc in query.stream():
            data = doc.to_dict() or {}
            records.append(
                PredictionRecord(
                    prediction_id=data.get("prediction_id", doc.id),
                    username=data.get("username", ""),
                    created_at=float(data.get("created_at", 0.0)),
                    request=data.get("request", {}),
                    result=data.get("result", {}),
                    metrics=data.get("metrics", {}),
                    meta=data.get("meta", {}),
                )
            )
        return records
from __future__ import annotations

from app.repositories.prediction_repository import PredictionRecord

try:
    import firebase_admin
    from firebase_admin import credentials, firestore
except ImportError:  # pragma: no cover - optional dependency
    firebase_admin = None
    credentials = None
    firestore = None


class FirestorePredictionRepository:
    def __init__(self, project_id: str, credentials_path: str = ""):
        if firebase_admin is None or firestore is None:
            raise RuntimeError("firebase-admin package is required for Firestore prediction repository.")
        if not firebase_admin._apps:
            cred = credentials.ApplicationDefault() if not credentials_path else credentials.Certificate(credentials_path)
            firebase_admin.initialize_app(cred, {"projectId": project_id} if project_id else None)
        self._db = firestore.client()
        self._collection = self._db.collection("predictions")

    def save_prediction(self, record: PredictionRecord) -> None:
        self._collection.document(record.prediction_id).set(
            {
                "prediction_id": record.prediction_id,
                "username": record.username,
                "created_at": record.created_at,
                "request": record.request,
                "result": record.result,
                "metrics": record.metrics,
                "meta": record.meta,
            },
            merge=True,
        )

    def list_predictions(self, username: str | None = None, limit: int = 20) -> list[PredictionRecord]:
        query = self._collection.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
        if username:
            query = query.where("username", "==", username)
        items: list[PredictionRecord] = []
        for doc in query.stream():
            data = doc.to_dict() or {}
            items.append(
                PredictionRecord(
                    prediction_id=data.get("prediction_id", doc.id),
                    username=data.get("username", ""),
                    created_at=float(data.get("created_at", 0.0)),
                    request=data.get("request", {}),
                    result=data.get("result", {}),
                    metrics=data.get("metrics", {}),
                    meta=data.get("meta", {}),
                )
            )
        return items
