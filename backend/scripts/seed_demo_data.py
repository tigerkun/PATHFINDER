import time
import uuid

from app.core.state import prediction_repository
from app.repositories.prediction_repository import PredictionRecord


def main():
    now = time.time()
    for idx in range(3):
        prediction_repository.save_prediction(
            PredictionRecord(
                prediction_id=str(uuid.uuid4()),
                username=f"demo-user-{idx}",
                created_at=now - (idx * 60),
                request={"username": f"demo-user-{idx}", "cgpa": 8.0, "tier": "tier2", "target": "backend_engineer", "status": "student"},
                result={"recommended_role": {"title": "Backend Engineer"}},
                metrics={"total_repos": 10 + idx},
                meta={"model": "demo", "prompt_version": "seed", "api_version": "2.3.0"},
            )
        )
    print("Seeded demo prediction records.")


if __name__ == "__main__":
    main()
