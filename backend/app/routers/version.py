from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["System"])


@router.get("/version")
async def get_version():
    return {
        "application": "ABB MLOps Platform API",
        "version": "0.1.0",
        "environment": "development",
    }
