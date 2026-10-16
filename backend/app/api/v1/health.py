from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(tags=["health"])

@router.get("/health")
async def health():
    return {"status": "ok", "time": datetime.now(tz=timezone.utc).isoformat(), "service": "CnizOS Backend"}

@router.get("/api/v1/health")
async def health_v1():
    return {"status": "ok", "time": datetime.now(tz=timezone.utc).isoformat()}
