from fastapi import APIRouter, Request

from app.core.config import API_VERSION, DEFAULTS, STATUSES, TARGETS, TIERS
from app.core.state import runtime_metrics
from services.api_models import ExamplesResponse, FormSchemaResponse, HealthResponse, MetricsResponse, OptionsResponse

router = APIRouter(prefix="/api/v1", tags=["meta"])


@router.get("/options", summary="Get frontend integration options/defaults", response_model=OptionsResponse)
async def options():
    return {
        "status": "success",
        "data": {
            "tier_options": TIERS,
            "target_options": TARGETS,
            "status_options": STATUSES,
            "defaults": DEFAULTS,
        },
    }


@router.get("/schema/form", summary="Get dynamic frontend form schema", response_model=FormSchemaResponse)
async def form_schema():
    return {
        "status": "success",
        "data": {
            "form_id": "career-predict-v1",
            "fields": [
                {
                    "name": "username",
                    "label": "GitHub Username",
                    "type": "text",
                    "required": True,
                    "placeholder": "torvalds",
                    "validation": {"min_length": 1, "max_length": 39, "pattern": "^[A-Za-z0-9-]+$"},
                    "help_text": "Only GitHub username, do not include full URL.",
                },
                {
                    "name": "cgpa",
                    "label": "CGPA / GPA",
                    "type": "number",
                    "required": True,
                    "min": 0,
                    "max": 10,
                    "step": 0.1,
                    "default": DEFAULTS["cgpa"],
                },
                {
                    "name": "tier",
                    "label": "College Tier",
                    "type": "select",
                    "required": True,
                    "options": list(TIERS),
                    "default": DEFAULTS["tier"],
                },
                {
                    "name": "target",
                    "label": "Target Domain",
                    "type": "select",
                    "required": True,
                    "options": list(TARGETS),
                    "default": DEFAULTS["target"],
                },
                {
                    "name": "status",
                    "label": "Current Status",
                    "type": "select",
                    "required": True,
                    "options": list(STATUSES),
                    "default": DEFAULTS["status"],
                },
            ],
        },
    }


@router.get("/examples", summary="Get example payloads for frontend and API clients", response_model=ExamplesResponse)
async def examples():
    return {
        "status": "success",
        "data": {
            "predict_request_examples": [
                {"username": "torvalds", "cgpa": 8.2, "tier": "tier1", "target": "backend_engineer", "status": "student"},
                {"username": "octocat", "cgpa": 7.4, "tier": "tier2", "target": "fullstack_engineer", "status": "fresher"},
            ],
            "profile_username_examples": ["torvalds", "octocat", "sindresorhus"],
        },
    }


@router.get("/health", summary="Service health", response_model=HealthResponse)
async def health(request: Request):
    return {
        "status": "ok",
        "request_id": getattr(request.state, "request_id", None),
        "api_version": API_VERSION,
    }


@router.get("/metrics", summary="Basic runtime metrics", response_model=MetricsResponse)
async def metrics():
    requests_total = runtime_metrics["requests_total"]
    average_latency_ms = (
        runtime_metrics["latency_ms_total"] / requests_total if requests_total else 0.0
    )
    return {
        "status": "success",
        "data": {
            "requests_total": requests_total,
            "average_latency_ms": round(average_latency_ms, 2),
            "requests_by_status": runtime_metrics["requests_by_status"],
            "top_paths": runtime_metrics["requests_by_path"],
        },
    }
