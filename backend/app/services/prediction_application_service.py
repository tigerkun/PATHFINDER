from __future__ import annotations

from app.domain.prediction import run_prediction, run_profile_metrics


class PredictionApplicationService:
    async def predict(self, username: str, cgpa: float, tier: str, target: str, status: str):
        return await run_prediction(username=username, cgpa=cgpa, tier=tier, target=target, status=status)

    async def profile(self, username: str):
        return await run_profile_metrics(username=username)
