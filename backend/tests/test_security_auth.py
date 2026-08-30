import os
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

os.environ["API_AUTH_KEY"] = "test-key-123456789"
os.environ["JWT_SECRET_KEY"] = "jwt-secret-for-tests"
os.environ["GITHUB_TOKEN"] = "test-token"
os.environ["GEMINI_API_KEY"] = "test-gemini"

from app.main import app  # noqa: E402
import app.core.security as security_module  # noqa: E402


client = TestClient(app)


def _make_jwt_token(secret: str) -> str:
    if security_module.jwt is None:
        return ""
    now = datetime.now(timezone.utc)
    payload = {"sub": "test-user", "exp": now + timedelta(minutes=5)}
    return security_module.jwt.encode(payload, secret, algorithm="HS256")


def test_jwt_auth_mode_accepts_valid_token(monkeypatch):
    monkeypatch.setattr(security_module, "AUTH_MODE", "jwt")
    async def fake_profile(_username):
        return {"status": "success", "data": {"username": "octocat"}}

    monkeypatch.setattr("app.routers.prediction.run_profile_metrics", fake_profile)
    token = _make_jwt_token("jwt-secret-for-tests")
    if not token:
        response = client.get("/api/v1/profile/octocat")
        assert response.status_code == 401
        return
    response = client.get("/api/v1/profile/octocat", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code != 401


def test_hybrid_mode_accepts_api_key(monkeypatch):
    monkeypatch.setattr(security_module, "AUTH_MODE", "hybrid")
    async def fake_profile(_username):
        return {"status": "success", "data": {"username": "octocat"}}

    monkeypatch.setattr("app.routers.prediction.run_profile_metrics", fake_profile)
    response = client.get("/api/v1/profile/octocat", headers={"X-API-Key": "test-key-123456789"})
    assert response.status_code != 401
