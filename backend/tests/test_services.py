import json
import asyncio
from types import SimpleNamespace

import httpx

from app.domain.prediction import map_profile_fetch_error
from services.ai_service import AIService
from services.github_service import GitHubService


def test_map_profile_fetch_error_variants():
    assert map_profile_fetch_error("GitHub user 'abc' not found") == (404, "PROFILE_NOT_FOUND")
    assert map_profile_fetch_error("GitHub API timed out. Please try again.") == (504, "GITHUB_TIMEOUT")
    assert map_profile_fetch_error("Invalid GitHub Token. Check your .env file.") == (502, "GITHUB_AUTH_FAILED")
    assert map_profile_fetch_error("Network error: boom") == (503, "GITHUB_NETWORK_ERROR")
    assert map_profile_fetch_error("some other upstream failure") == (502, "GITHUB_UPSTREAM_ERROR")


def test_github_service_timeout(monkeypatch):
    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            raise httpx.TimeoutException("timeout")

    monkeypatch.setattr("services.github_service.httpx.AsyncClient", lambda *a, **k: FakeAsyncClient())
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    result = asyncio.run(GitHubService().fetch_all("octocat"))
    assert result["error"] == "GitHub API timed out. Please try again."


def test_github_service_network_error(monkeypatch):
    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            raise httpx.RequestError("offline", request=httpx.Request("POST", "https://api.github.com/graphql"))

    monkeypatch.setattr("services.github_service.httpx.AsyncClient", lambda *a, **k: FakeAsyncClient())
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    result = asyncio.run(GitHubService().fetch_all("octocat"))
    assert "Network error:" in result["error"]


def test_github_service_user_not_found(monkeypatch):
    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"errors": [{"message": "Could not resolve to a User with the login of 'missing'."}]}

    class FakeAsyncClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc, tb):
            return False

        async def post(self, *args, **kwargs):
            return FakeResponse()

    monkeypatch.setattr("services.github_service.httpx.AsyncClient", lambda *a, **k: FakeAsyncClient())
    monkeypatch.setenv("GITHUB_TOKEN", "x")
    result = asyncio.run(GitHubService().fetch_all("missing"))
    assert result["error"] == "GitHub user 'missing' not found"


def test_ai_service_invalid_json(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    class FakeResponse:
        text = "not-json-response"

    class FakeModel:
        async def generate_content(self, _prompt, **_kwargs):
            return FakeResponse()

    monkeypatch.setattr(
        "services.ai_service.genai",
        SimpleNamespace(configure=lambda **kwargs: None, GenerativeModel=lambda *_args, **_kwargs: FakeModel()),
    )

    ai = AIService()
    result = asyncio.run(ai.analyze({"a": 1}, {"cgpa": 8}))
    assert "fallback_error" in result
    assert result["recommended_role"]["title"] == "Generalist Engineer"


def test_ai_service_fills_missing_defaults(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "test-key")

    report_payload = {
        "recommended_role": {
            "title": "Backend Engineer",
            "definition": "Backend developer",
            "scope": "Core APIs",
            "confidence": 92
        },
        "alternative_roles": [{"title": "DevOps Engineer", "fit_score": 85}],
        "indian_salary": {"fresher": "₹6-10 LPA", "mid": "₹12-22 LPA", "senior": "₹25-45 LPA"},
        "match_pct": 88,
        "profile_score": {"overall": 88, "activity": 85, "diversity": 90, "open_source": 75, "consistency": 86},
        "strengths": ["Python", "FastAPI architecture"],
        "gaps": ["Kubernetes"],
        "action_items": ["Containerize microservices"],
        "roadmap": [{"phase": "Phase 1", "weeks": "1-4", "focus": "Docker", "tasks": ["Build image"], "milestone": "Deploy"}],
        "top_companies": ["Google", "Stripe"],
        "verdict": "High-potential backend engineer."
    }

    class FakeResponse:
        text = json.dumps(report_payload)

    class FakeModel:
        async def generate_content(self, _prompt, **_kwargs):
            return FakeResponse()

    monkeypatch.setattr(
        "services.ai_service.genai",
        SimpleNamespace(configure=lambda **kwargs: None, GenerativeModel=lambda *_args, **_kwargs: FakeModel()),
    )

    ai = AIService()
    result = asyncio.run(ai.analyze({"a": 1}, {"cgpa": 8}))
    assert result["recommended_role"]["title"] == "Backend Engineer"
    assert "verdict" in result
    assert "profile_score" in result
