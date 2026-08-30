import sys
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.config import JOB_TTL_SECONDS
from app.core.state import job_service


def main():
    job_service.cleanup_old_jobs(JOB_TTL_SECONDS)
    print("Old jobs cleanup completed.")


if __name__ == "__main__":
    main()
