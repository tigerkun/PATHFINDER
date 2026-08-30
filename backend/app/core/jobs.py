from app.core.config import JOB_TTL_SECONDS
from app.core.state import job_service


def snapshot_job(job_id: str):
    job = job_service.get_job(job_id)
    if not job:
        return None
    return {
        "status": job.status,
        "created_at": job.created_at,
        "updated_at": job.updated_at,
        "request": job.request,
        "result": job.result,
        "error": job.error,
        "task": None,
    }


def persist_job(_job_id: str):
    return None


def cleanup_old_jobs():
    job_service.cleanup_old_jobs(JOB_TTL_SECONDS)


def start_prediction_job(job_id: str, payload, run_prediction):
    job = job_service.get_job(job_id)
    if not job:
        return
    job_service.enqueue_prediction_job(job=job, run_prediction=run_prediction)
