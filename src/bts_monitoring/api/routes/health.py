from fastapi import APIRouter

router = APIRouter(prefix="/health", tags=["health"])


@router.get("/live")
async def liveness() -> dict[str, bool]:
    return {"ok": True}


@router.get("/ready")
async def readiness() -> dict[str, bool]:
    return {
        "ok": True,
        "database": True,
        "redis": True,
    }