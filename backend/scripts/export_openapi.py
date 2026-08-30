import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app


def main() -> None:
    out_dir = ROOT / "frontend-sdk"
    out_dir.mkdir(parents=True, exist_ok=True)

    openapi_path = out_dir / "openapi.json"
    openapi_path.write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")

    print(f"OpenAPI spec exported: {openapi_path}")
    print("Next step (Node required):")
    print(
        "npx openapi-typescript frontend-sdk/openapi.json "
        "--output frontend-sdk/api-types.ts"
    )


if __name__ == "__main__":
    main()
