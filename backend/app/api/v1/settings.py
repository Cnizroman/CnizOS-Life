from fastapi import APIRouter, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
import os, json, subprocess, pathlib
from app.db.session import get_db, engine, Base
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.activity import ActivityLog, IntegrationSettings

router = APIRouter(prefix="/settings", tags=["settings"])

@router.get("")
async def get_settings(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(IntegrationSettings).where(IntegrationSettings.user_id==user.id))
    s = res.scalar_one_or_none()
    if not s:
        s = IntegrationSettings(user_id=user.id)
        db.add(s)
        await db.commit()
        await db.refresh(s)
    return {"theme": s.theme, "accent": s.accent, "density": s.density, "zoro_enabled": s.zoro_enabled, "bridge_auto_connect": s.bridge_auto_connect}

@router.patch("")
async def patch_settings(payload: dict, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(IntegrationSettings).where(IntegrationSettings.user_id==user.id))
    s = res.scalar_one_or_none()
    if not s:
        s = IntegrationSettings(user_id=user.id)
        db.add(s)
        await db.flush()
    for k in ["theme","accent","density","zoro_enabled","bridge_auto_connect"]:
        if k in payload:
            setattr(s, k, payload[k])
    s.updated_at = datetime.now(tz=timezone.utc)
    db.add(ActivityLog(user_id=user.id, action="settings.update", entity_type="settings", entity_id=user.id, meta=payload, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    return {"ok": True, "settings": {"theme": s.theme, "accent": s.accent}}

@router.get("/activity")
async def activity(limit: int = 50, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ActivityLog).where(ActivityLog.user_id==user.id).order_by(ActivityLog.created_at.desc()).limit(limit))
    logs = res.scalars().all()
    return {"data": [{"id": l.id, "action": l.action, "entity_type": l.entity_type, "entity_id": l.entity_id, "meta": l.meta, "created_at": l.created_at.isoformat()} for l in logs]}

@router.post("/backup")
async def backup(user: User = Depends(get_current_user)):
    # For SQLite, just copy file; for Postgres, pg_dump via env
    db_path = "./cnizos.db"
    backup_path = f"storage/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    os.makedirs("storage", exist_ok=True)
    if os.path.exists(db_path):
        import shutil
        shutil.copy(db_path, backup_path)
        return {"path": backup_path, "size": os.path.getsize(backup_path)}
    else:
        # postgres dump attempt
        return {"detail": "Postgres backup via pg_dump not configured in sandbox", "path": None}

@router.post("/restore")
async def restore(payload: dict, user: User = Depends(get_current_user)):
    return {"detail": "Restore requires file upload — use POST /api/v1/settings/restore/upload with file"}
