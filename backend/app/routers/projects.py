from fastapi import APIRouter

router = APIRouter(prefix="/api/projects", tags=["Projects"])


@router.get("")
async def get_projects():
    return {
        "items": [],
        "count": 0,
    }
