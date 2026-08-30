import os

from fastapi.testclient import TestClient

os.environ["API_AUTH_KEY"] = "test-key-123456789"
os.environ["GITHUB_TOKEN"] = "test-token"
os.environ["GEMINI_API_KEY"] = "test-gemini"
os.environ["JWT_SECRET_KEY"] = "jwt-secret-for-tests"

from app.main import app  # noqa: E402
from app.core.state import runtime_metrics  # noqa: E402


client = TestClient(app)


def test_health_endpoint_available():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "api_version" in data


def test_protected_endpoint_requires_api_key():
    response = client.get("/api/v1/profile/octocat")
    assert response.status_code == 401
    body = response.json()
    assert body["error"]["code"] == "UNAUTHORIZED"


def test_options_endpoint_available():
    response = client.get("/api/v1/options")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "defaults" in body["data"]


def test_predict_post_success_with_api_key(monkeypatch):
    async def fake_run_prediction(username, cgpa, tier, target, status):
        return {
            "status": "success",
            "data": {"recommended_role": {"title": "Backend Engineer"}},
            "metrics": {"total_repos": 12},
            "request": {
                "username": username,
                "cgpa": cgpa,
                "tier": tier,
                "target": target,
                "status": status,
            },
            "meta": {"model": "fake", "prompt_version": "test", "api_version": "test"},
        }

    monkeypatch.setattr("app.routers.prediction.run_prediction", fake_run_prediction)
    payload = {
        "username": "octocat",
        "cgpa": 8.0,
        "tier": "tier2",
        "target": "backend_engineer",
        "status": "student",
    }
    response = client.post("/api/v1/predict", json=payload, headers={"X-API-Key": "test-key-123456789"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["request"]["username"] == "octocat"


def test_predict_rate_limit_exceeded(monkeypatch):
    def fake_check_rate_limit(_):
        return False, 0, 13

    monkeypatch.setattr("app.routers.prediction.check_rate_limit", fake_check_rate_limit)
    payload = {
        "username": "octocat",
        "cgpa": 8.0,
        "tier": "tier2",
        "target": "backend_engineer",
        "status": "student",
    }
    response = client.post("/api/v1/predict", json=payload, headers={"X-API-Key": "test-key-123456789"})
    assert response.status_code == 429
    body = response.json()
    assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"


def test_job_create_and_cancel_flow(monkeypatch):
    async def fake_run_prediction(username, cgpa, tier, target, status):
        return {
            "status": "success",
            "data": {"recommended_role": {"title": "Backend Engineer"}},
            "metrics": {"total_repos": 2},
            "request": {
                "username": username,
                "cgpa": cgpa,
                "tier": tier,
                "target": target,
                "status": status,
            },
            "meta": {"model": "fake", "prompt_version": "test", "api_version": "test"},
        }

    monkeypatch.setattr("app.routers.prediction.run_prediction", fake_run_prediction)
    payload = {
        "username": "octocat",
        "cgpa": 7.8,
        "tier": "tier2",
        "target": "backend_engineer",
        "status": "student",
    }
    create = client.post("/api/v1/predict/jobs", json=payload, headers={"X-API-Key": "test-key-123456789"})
    assert create.status_code == 200
    job_id = create.json()["job_id"]

    cancel = client.delete(f"/api/v1/predict/jobs/{job_id}", headers={"X-API-Key": "test-key-123456789"})
    assert cancel.status_code == 200
    assert cancel.json()["data"]["job_status"] in {"cancelled", "completed"}


def test_metrics_endpoint_shape():
    response = client.get("/api/v1/metrics")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "requests_total" in body["data"]
    assert "requests_by_status" in body["data"]
    assert body["data"]["requests_total"] >= 1


def test_runtime_metrics_counter_increments():
    before = runtime_metrics["requests_total"]
    client.get("/api/v1/health")
    after = runtime_metrics["requests_total"]
    assert after > before


def test_list_jobs_endpoint_available():
    response = client.get("/api/v1/predict/jobs", headers={"X-API-Key": "test-key-123456789"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "items" in body["data"]


def test_analytics_and_ops_endpoints():
    usage = client.get("/api/v1/analytics/usage", headers={"X-API-Key": "test-key-123456789"})
    assert usage.status_code == 200
    assert usage.json()["status"] == "success"

    latency = client.get("/api/v1/analytics/latency", headers={"X-API-Key": "test-key-123456789"})
    assert latency.status_code == 200
    assert latency.json()["status"] == "success"

    live = client.get("/api/v1/live")
    assert live.status_code == 200
    assert live.json()["status"] == "ok"

    ready = client.get("/api/v1/ready")
    assert ready.status_code == 200
    assert ready.json()["status"] == "ready"
