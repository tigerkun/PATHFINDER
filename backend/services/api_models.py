from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class ApiErrorDetail(BaseModel):
    code: str
    message: str
    request_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ApiErrorResponse(BaseModel):
    status: Literal["error"] = "error"
    error: ApiErrorDetail


class PredictRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=39, pattern=r"^[A-Za-z0-9-]+$")
    cgpa: float = Field(default=7.0, ge=0, le=10)
    tier: Literal["tier1", "tier2", "tier3"] = "tier2"
    target: Literal[
        "software_engineer",
        "backend_engineer",
        "frontend_engineer",
        "fullstack_engineer",
        "ml_engineer",
        "data_engineer",
        "devops_engineer",
        "mobile_engineer",
        "security_engineer",
    ] = "software_engineer"
    status: Literal["student", "fresher", "experienced", "senior"] = "student"

    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "torvalds",
                "cgpa": 8.2,
                "tier": "tier1",
                "target": "backend_engineer",
                "status": "student",
            }
        }
    }


class JobCreateResponse(BaseModel):
    status: Literal["accepted"] = "accepted"
    job_id: str
    poll_url: str


class JobStatusData(BaseModel):
    job_id: str
    job_status: Literal["queued", "running", "completed", "failed", "cancelled"]
    created_at: float
    updated_at: float
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None


class JobStatusResponse(BaseModel):
    status: Literal["success"] = "success"
    data: JobStatusData


class JobListResponse(BaseModel):
    status: Literal["success"] = "success"
    data: Dict[str, Any]


class PredictMeta(BaseModel):
    model: str
    prompt_version: str
    api_version: str


class PredictSuccessResponse(BaseModel):
    status: Literal["success"] = "success"
    data: Dict[str, Any]
    metrics: Dict[str, Any]
    request: Dict[str, Any]
    meta: PredictMeta


class ProfileResponse(BaseModel):
    status: Literal["success"] = "success"
    data: Dict[str, Any]


class OptionsResponse(BaseModel):
    status: Literal["success"] = "success"
    data: Dict[str, Any]


class FormSchemaResponse(BaseModel):
    status: Literal["success"] = "success"
    data: Dict[str, Any]


class ExamplesResponse(BaseModel):
    status: Literal["success"] = "success"
    data: Dict[str, Any]


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    request_id: Optional[str] = None
    api_version: str


class MetricsResponse(BaseModel):
    status: Literal["success"] = "success"
    data: Dict[str, Any]


class AnalyticsResponse(BaseModel):
    status: Literal["success"] = "success"
    data: Dict[str, Any]

