from app.core.config import JOB_TTL_SECONDS
from app.core.state import job_service


def main():
    job_service.cleanup_old_jobs(JOB_TTL_SECONDS)
    print("Old jobs cleanup completed.")


if __name__ == "__main__":
    main()
