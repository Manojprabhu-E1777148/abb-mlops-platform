from datetime import datetime, timezone

from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health", status_code=200)
def get_health() -> dict[str, str]:
    return {
        "status": "Healthy",
        "service": "ABB MLOps Platform API",
        "timestampUtc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
