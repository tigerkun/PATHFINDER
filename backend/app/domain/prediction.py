from services.api_models import PredictSuccessResponse, ProfileResponse

from app.core.config import API_VERSION
from app.core.errors import api_error
from app.core.state import get_ai_engine, gh_engine
from typing import Dict, Any


class PathfinderScorer:
    """
    Proprietary heuristic engine to calculate the 'Innovation Quotient' (IQ).
    IQ = (StackRarity * 0.4) + (CommitDensity * 0.3) + (ProjectComplexity * 0.3)
    """
    # Weights for the IQ calculation
    WEIGHTS = {
        "rarity": 0.4,
        "density": 0.3,
        "complexity": 0.3
    }

    # Rarity mapping for languages (simplified heuristic)
    RARITY_MAP = {
        "rust": 100, "go": 80, "cpp": 70, "swift": 70,
        "python": 40, "javascript": 30, "java": 30, "html": 10
    }

    def calculate_iq(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Tech-Stack Rarity (Avg rarity of top 3 languages)
        langs = metrics.get("languages", {})
        if not langs:
            rarity_score = 0
        else:
            top_langs = sorted(langs.items(), key=lambda x: x[1], reverse=True)[:3]
            rarity_score = sum(self.RARITY_MAP.get(l.lower(), 20) for l, _ in top_langs) / len(top_langs)

        # 2. Commit Density (Simplified: normalized against expected high activity)
        commits = metrics.get("total_commits", 0)
        density_score = min(100, (commits / 500) * 100)

        # 3. Project Complexity (Simplified: avg stars * forks per project)
        repos = metrics.get("repositories", [])
        if not repos:
            complexity_score = 0
        else:
            scores = [ (r.get("stars", 0) * 2 + r.get("forks", 0)) for r in repos ]
            complexity_score = min(100, (sum(scores) / len(repos)) * 10)

        iq = (rarity_score * self.WEIGHTS["rarity"] +
              density_score * self.WEIGHTS["density"] +
              complexity_score * self.WEIGHTS["complexity"])

        return {
            "innovation_quotient": round(iq, 2),
            "breakdown": {
                "tech_rarity": round(rarity_score, 2),
                "commit_density": round(density_score, 2),
                "complexity": round(complexity_score, 2)
            }
        }

    def simulate_improvement(self, current_iq_data: Dict[str, Any]) -> Dict[str, Any]:
        breakdown = current_iq_data["breakdown"]
        # Identify lowest metric
        lowest_metric = min(breakdown, key=breakdown.get)
        current_val = breakdown[lowest_metric]

        # Simulate 15% boost to that specific metric (capped at 100)
        boosted_val = min(100, current_val * 1.15)
        diff = boosted_val - current_val

        # Calculate Target IQ based on the weight of the boosted metric
        weight = self.WEIGHTS[lowest_metric.replace("tech_", "").replace("_score", "")]
        # Note: mapping keys 'tech_rarity' -> 'rarity', etc.
        if "tech_rarity" in lowest_metric: weight = self.WEIGHTS["rarity"]
        elif "commit_density" in lowest_metric: weight = self.WEIGHTS["density"]
        elif "complexity" in lowest_metric: weight = self.WEIGHTS["complexity"]

        target_iq = current_iq_data["innovation_quotient"] + (diff * weight)

        return {
            "target_iq": round(target_iq, 2),
            "primary_growth_lever": lowest_metric.replace("_", " ").title(),
            "expected_boost": round(target_iq - current_iq_data["innovation_quotient"], 2)
        }


def normalize_username(username: str) -> str:
    return username.strip().lstrip("@")


def map_profile_fetch_error(message: str) -> tuple[int, str]:
    msg = (message or "").lower()
    if "not found" in msg:
        return 404, "PROFILE_NOT_FOUND"
    if "timed out" in msg:
        return 504, "GITHUB_TIMEOUT"
    if "invalid github token" in msg:
        return 502, "GITHUB_AUTH_FAILED"
    if "network error" in msg:
        return 503, "GITHUB_NETWORK_ERROR"
    return 502, "GITHUB_UPSTREAM_ERROR"


async def run_prediction(username: str, cgpa: float, tier: str, target: str, status: str):
    username = normalize_username(username)
    if not username:
        return api_error(None, 400, "INVALID_USERNAME", "Username is required")
    if cgpa < 0 or cgpa > 10:
        return api_error(None, 400, "INVALID_CGPA", "CGPA must be between 0 and 10")

    metrics = await gh_engine.fetch_all(username)
    if "error" in metrics:
        status_code, error_code = map_profile_fetch_error(metrics["error"])
        return api_error(None, status_code, error_code, metrics["error"])

    context = {"cgpa": cgpa, "tier": tier, "target": target, "status": status}
    ai = get_ai_engine()
    report = await ai.analyze(metrics, context)
    if "error" in report:
        return api_error(None, 500, "AI_ANALYSIS_FAILED", report["error"])

    # Technical Sovereignty: Merge AI insight with custom heuristic scoring
    scorer = PathfinderScorer()
    iq_data = scorer.calculate_iq(metrics)
    report["innovation_quotient"] = iq_data["innovation_quotient"]
    report["iq_breakdown"] = iq_data["breakdown"]

    # What-If Simulation
    report["prediction_delta"] = scorer.simulate_improvement(iq_data)

    meta = ai.get_metadata() | {"api_version": API_VERSION}
    return PredictSuccessResponse(
        data=report,
        metrics=metrics,
        request=context | {"username": username},
        meta=meta,
    ).model_dump()


async def run_profile_metrics(username: str):
    username = normalize_username(username)
    if not username:
        return api_error(None, 400, "INVALID_USERNAME", "Username is required")
    metrics = await gh_engine.fetch_all(username)
    if "error" in metrics:
        status_code, error_code = map_profile_fetch_error(metrics["error"])
        return api_error(None, status_code, error_code, metrics["error"])
    return ProfileResponse(data=metrics).model_dump()
