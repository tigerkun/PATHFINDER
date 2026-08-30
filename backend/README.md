# Backend API Guide

This backend exposes HTML pages and JSON APIs for frontend clients.

## Security Tracking

- Active register: `VULNERABILITY_REGISTER.md`
- Source battle plan canvas: `pathfinder-security-battle-plan.canvas.tsx`

## Base URL

- Local: `http://localhost:8000`
- OpenAPI docs: `http://localhost:8000/docs`

## Core Endpoints

- `GET /api/v1/health`
  - Health check, runtime config flags, request id.

- `GET /api/v1/metrics`
  - Basic runtime metrics (request count, status distribution, average latency).

- `GET /api/v1/options`
  - Returns frontend dropdown options and default values.

- `GET /api/v1/profile/{username}`
  - Fast mode: GitHub metrics only, no AI analysis.

- `GET /api/v1/predict/{username}`
  - Backward-compatible prediction endpoint using query params:
  - `cgpa`, `tier`, `target`, `status`

- `POST /api/v1/predict`
  - Preferred prediction endpoint for frontend clients.
  - JSON body example:
    ```json
    {
      "username": "torvalds",
      "cgpa": 8.2,
      "tier": "tier1",
      "target": "backend_engineer",
      "status": "student"
    }
    ```

- `POST /api/v1/predict/jobs`
  - Creates an async prediction job for long-running analysis.
  - Returns `job_id` and `poll_url`.

- `GET /api/v1/predict/jobs/{job_id}`
  - Poll async job status (`queued`, `running`, `completed`, `failed`, `cancelled`).

- `GET /api/v1/predict/jobs`
  - List async prediction jobs with optional `status` and `limit`.

- `POST /api/v1/predict/jobs/{job_id}/retry`
  - Retry a failed/cancelled job.

- `GET /api/v1/predict/jobs/{job_id}/events`
  - SSE stream for live job status updates (push-based alternative to polling).

- `DELETE /api/v1/predict/jobs/{job_id}`
  - Cancels an in-flight async job.

- `GET /api/v1/predictions/history`
  - Prediction history with optional `username` filter and `limit`.

- `GET /api/v1/analytics/usage`
  - Prediction usage snapshot and daily request rollups.

- `GET /api/v1/analytics/latency`
  - Runtime latency snapshot.

- `GET /api/v1/live`, `GET /api/v1/ready`
  - Liveness/readiness endpoints for deployment orchestration.

- `GET /api/v1/schema/form`
  - Returns dynamic form schema (labels, validation, defaults, option lists).

- `GET /api/v1/examples`
  - Returns sample payloads for quick frontend and API testing.

## Observability Headers

Every response includes:

- `X-Request-ID`: unique request identifier
- `X-Process-Time-ms`: end-to-end processing time

Prediction endpoints also include:

- `X-RateLimit-Remaining`: requests left in current window
- `Retry-After` (on `429`): seconds until next allowed request

## Standard Error Shape

All API errors return this structure:

```json
{
  "status": "error",
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Please retry later.",
    "request_id": "7d18f9bc-9f28-4e16-b34e-18f5d4d9f8af",
    "details": {
      "retry_after_seconds": 42
    }
  }
}
```

External dependency errors are now categorized into explicit codes such as:
- `PROFILE_NOT_FOUND`
- `GITHUB_TIMEOUT`
- `GITHUB_NETWORK_ERROR`
- `GITHUB_AUTH_FAILED`
- `GITHUB_UPSTREAM_ERROR`

## Environment Variables

- `GITHUB_TOKEN`: GitHub token for API calls
- `GEMINI_API_KEY`: Gemini key for AI analysis
- `API_AUTH_KEY`: required API key sent via `X-API-Key` for protected endpoints
- `API_AUTH_MIN_LENGTH`: minimum allowed auth key length (default `16`)
- `AUTH_MODE`: `api_key`, `jwt`, or `hybrid` (default `hybrid`)
- `JWT_SECRET_KEY`: signing secret for JWT validation (required in `jwt`/`hybrid`)
- `JWT_ALGORITHM`: JWT algorithm (default `HS256`)
- `JWT_ISSUER`: optional JWT issuer validation
- `JWT_AUDIENCE`: optional JWT audience validation
- `CORS_ALLOW_ORIGINS`: comma-separated origins
- `ENABLE_SECURITY_HEADERS`: enable secure response headers (default `true`)
- `CONTENT_SECURITY_POLICY`: CSP header value used when security headers are enabled
- `APP_ENV`: environment name (`development` by default, use `production` to enforce Redis rate limiting)
- `DATA_BACKEND`: `sqlite` or `supabase` (default `sqlite`)
- `SUPABASE_URL`: Supabase project URL (required for `DATA_BACKEND=supabase`)
- `SUPABASE_SERVICE_KEY`: service role key (required for `DATA_BACKEND=supabase`)
- `SUPABASE_JOBS_TABLE`: jobs table name (default `jobs`)
- `SUPABASE_PREDICTIONS_TABLE`: predictions table name (default `predictions`)
- `QUEUE_BACKEND`: async queue backend (current: `inprocess`)
- `RATE_LIMIT_WINDOW_SECONDS`: rate-limit window (default `60`)
- `RATE_LIMIT_MAX_REQUESTS`: max requests per IP in window (default `15`)
- `RATE_LIMIT_BACKEND`: `memory` or `redis` (default `memory`)
- `RATE_LIMIT_REDIS_URL`: Redis URL used when `RATE_LIMIT_BACKEND=redis`
- `JOB_TTL_SECONDS`: async job retention in memory (default `3600`)

## Running

1. Install dependencies:
   - `pip install -r requirements.txt`
   - Lock update workflow (when dependencies change):
     - edit `requirements.in`
     - run `python -m piptools compile requirements.in --output-file requirements.txt`
2. Copy `.env.example` to `.env` and set real values.
3. For Supabase mode, run SQL in `scripts/supabase_schema.sql` in your Supabase SQL editor.
4. Start server from `backend/`:
   - `uvicorn app.main:app --reload`

## Frontend SDK Generation Path

From `backend/`:

1. Export OpenAPI spec:
   - `python scripts/export_openapi.py`
2. Generate TypeScript API types:
   - `npx openapi-typescript frontend-sdk/openapi.json --output frontend-sdk/api-types.ts`

You can import generated types in your frontend API layer to keep contracts synchronized.
There is also a starter typed client at `frontend-sdk/api-client.ts`.

For browser SSE (`EventSource`), use the stream URL helper from the client.
It authenticates via `api_key` query param because `EventSource` cannot send `X-API-Key` headers.

## Frontend Integration Notes

- For fast pre-checks, call `/api/v1/profile/{username}` before full prediction.
- Use `/api/v1/options` to dynamically render form dropdowns.
- Use `/api/v1/schema/form` to generate forms without hardcoding validation rules.
- Use `/api/v1/examples` for seeded demo/test inputs.
- For better UX on slow networks, use async jobs (`/predict/jobs`) and poll status.
