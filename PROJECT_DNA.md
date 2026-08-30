# 🧬 PROJECT DNA: Pathfinder Career Intelligence Engine

## 🌌 Project Essence
Pathfinder is a high-precision career intelligence system that transforms raw GitHub activity into actionable career trajectories. It moves beyond generic AI wrappers by combining **LLM-driven qualitative analysis** (via Gemini 1.5 Flash) with a **proprietary quantitative heuristic engine** (PathfinderScorer) to provide an 'Innovation Quotient' (IQ) and predictive 'What-If' simulations.

## 🛠️ Engineering Blueprint

### 1. Architecture & Concurrency
- **Async-First:** The system is fully non-blocking. The repository layer uses `httpx.AsyncClient` to interact with Supabase, and the AI service is integrated via `async/await` to prevent event-loop starvation.
- **Resilient Schema:** Implements **Pydantic v2** for strict structured outputs. AI responses are validated against a rigorous schema (`AIReport`), with a "Safe Report" fallback mechanism to ensure 100% API availability even during LLM hallucinations.

### 2. The 'Secret Sauce': PathfinderScorer
The engine calculates the **Innovation Quotient (IQ)** using a weighted heuristic:
`IQ = (StackRarity * 0.4) + (CommitDensity * 0.3) + (ProjectComplexity * 0.3)`
- **Stack Rarity:** Weighted mapping of languages (e.g., Rust > Python).
- **Commit Density:** Normalized contribution volume.
- **Project Complexity:** Derived from stars/forks ratios.
- **Simulation:** A 'What-If' engine identifies the weakest growth lever and calculates a 15% boost scenario to provide a `prediction_delta`.

## 📡 API Specification

### `POST /predict`
**Request:** `{ "username": str, "cgpa": float, "tier": str, "target": str, "status": str }`

**Response Structure:**
- `data`: 
    - `recommended_role`: { title, definition, scope, confidence }
    - `profile_score`: { overall, activity, diversity, open_source, consistency }
    - `innovation_quotient`: float (The proprietary score)
    - `iq_breakdown`: { tech_rarity, commit_density, complexity }
    - `prediction_delta`: { target_iq, primary_growth_lever, expected_boost }
    - `roadmap`: List of phases with tasks and milestones.
- `metrics`: Raw GitHub data.
- `meta`: API version and model info.

### 📦 Sample Response
```json
{
  "data": {
    "recommended_role": { "title": "Distributed Systems Engineer", "confidence": 92 },
    "innovation_quotient": 74.5,
    "iq_breakdown": { "tech_rarity": 85, "commit_density": 60, "complexity": 70 },
    "prediction_delta": {
      "target_iq": 78.2,
      "primary_growth_lever": "Commit Density",
      "expected_boost": 3.7
    },
    "verdict": "Elite potential in systems programming with a need for more consistent public output."
  },
  "meta": { "model": "gemini-1.5-flash", "api_version": "2.3.0" }
}
```
