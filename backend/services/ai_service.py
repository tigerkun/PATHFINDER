import os
import json
import re
from typing import Dict

try:
    import google.generativeai as genai  # type: ignore
    GENAI_IMPORT_ERROR = None
except Exception as e:  # pragma: no cover - environment-specific import failures
    genai = None
    GENAI_IMPORT_ERROR = str(e)


from typing import Dict, Any, List
from pydantic import BaseModel, Field

class RoleInfo(BaseModel):
    title: str
    definition: str
    scope: str
    confidence: int

class AltRole(BaseModel):
    title: str
    fit_score: int

class SalaryInfo(BaseModel):
    fresher: str
    mid: str
    senior: str

class ProfileScore(BaseModel):
    overall: int
    activity: int
    diversity: int
    open_source: int
    consistency: int

class RoadmapPhase(BaseModel):
    phase: str
    weeks: str
    focus: str
    tasks: List[str]
    milestone: str

class AIReport(BaseModel):
    recommended_role: RoleInfo
    alternative_roles: List[AltRole]
    indian_salary: SalaryInfo
    match_pct: int
    profile_score: ProfileScore
    strengths: List[str]
    gaps: List[str]
    action_items: List[str]
    roadmap: List[RoadmapPhase]
    top_companies: List[str]
    verdict: str

class AIService:
    MODEL_NAME = "gemini-1.5-flash"
    PROMPT_VERSION = "2026-04-27.v2"

    def __init__(self):
        api_key = os.getenv("GEMINI_API_KEY")
        self.model = None
        self.init_error = None
        if genai is None:
            self.init_error = f"Gemini SDK import failed: {GENAI_IMPORT_ERROR}"
            return
        if not api_key:
            self.init_error = "GEMINI_API_KEY is not set in .env file"
            return
        try:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(self.MODEL_NAME)
        except Exception as e:
            self.init_error = f"Failed to initialize Gemini client: {str(e)}"

    def get_metadata(self) -> Dict:
        return {
            "model": self.MODEL_NAME,
            "prompt_version": self.PROMPT_VERSION,
        }

    async def analyze(self, metrics: Dict, context: Dict) -> Dict:
        if not self.model:
            return {"error": self.init_error or "Gemini client is not initialized"}

        prompt = self._build_prompt(metrics, context)
        try:
            # Use structured output via response_mime_type
            response = await self.model.generate_content(
                prompt,
                generation_config={"response_mime_type": "application/json"}
            )

            # Pydantic validation replaces regex/json.loads
            parsed = AIReport.model_validate_json(response.text)
            return parsed.model_dump()

        except Exception as e:
            # Fallback to a "Safe Report" instead of raw error to maintain resilience
            return self._get_safe_fallback(e)

    def _get_safe_fallback(self, error: Exception) -> Dict:
        return {
            "recommended_role": {"title": "Generalist Engineer", "definition": "Versatile software dev", "scope": "Fallback analysis", "confidence": 50},
            "alternative_roles": [],
            "indian_salary": {"fresher": "₹4-8 LPA", "mid": "₹10-18 LPA", "senior": "₹20-35 LPA"},
            "match_pct": 50,
            "profile_score": {"overall": 50, "activity": 50, "diversity": 50, "open_source": 50, "consistency": 50},
            "strengths": ["Profile processed with fallback"],
            "gaps": ["AI validation failed"],
            "action_items": ["Verify GitHub data"],
            "roadmap": [],
            "top_companies": ["Industry Standard"],
            "verdict": "Analysis completed via safety fallback.",
            "fallback_error": str(error)
        }

    def _build_prompt(self, metrics: Dict, context: Dict) -> str:
        # ... (Keep prompt logic, but remove "Return ONLY JSON" as we use mime_type)
        return f"""
You are an elite 2026 Indian tech recruiter. Analyze this GitHub profile.
GITHUB METRICS: {json.dumps(metrics)}
CONTEXT: {json.dumps(context)}
Output a precise career intelligence report following the requested JSON schema.
"""