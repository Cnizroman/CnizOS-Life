from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.activity import Device

router = APIRouter(prefix="/devices", tags=["devices"])

@router.post("/register")
async def register(payload: dict, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    import uuid
    dev = Device(user_id=user.id, name=payload.get("name","Browser"), platform=payload.get("platform","web"), push_subscription=payload.get("push_subscription"))
    db.add(dev)
    await db.commit()
    await db.refresh(dev)
    return {"id": dev.id, "name": dev.name}

@router.get("")
async def list_devices(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Device).where(Device.user_id==user.id).order_by(Device.last_seen_at.desc()))
    items = res.scalars().all()
    return {"data": [{"id": d.id, "name": d.name, "platform": d.platform, "last_seen_at": d.last_seen_at.isoformat()} for d in items]}

@router.delete("/{did}")
async def delete_device(did: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Device).where(Device.id==did, Device.user_id==user.id))
    d = res.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Device not found")
    await db.delete(d)
    await db.commit()
    return {"ok": True}
