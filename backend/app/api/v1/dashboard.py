from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timezone, timedelta
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.note import Note
from app.models.bridge import BridgeDevice, BridgeCommand

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary")
async def summary(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    now = datetime.now(tz=timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    # today tasks
    t_today = await db.execute(select(func.count()).select_from(Task).where(Task.user_id==user.id, Task.due_date>=today_start, Task.due_date < today_end))
    today_count = t_today.scalar() or 0
    t_overdue = await db.execute(select(func.count()).select_from(Task).where(Task.user_id==user.id, Task.due_date < now, Task.status.notin_(["done","cancelled"])))
    overdue_count = t_overdue.scalar() or 0
    p_active = await db.execute(select(func.count()).select_from(Project).where(Project.user_id==user.id, Project.status=="active", Project.archived_at.is_(None)))
    active_count = p_active.scalar() or 0
    # recent notes
    n_res = await db.execute(select(Note).where(Note.user_id==user.id, Note.is_archived==False).order_by(Note.updated_at.desc()).limit(5))
    recent_notes = [{"id": n.id, "title": n.title, "snippet": n.body[:100]} for n in n_res.scalars().all()]
    # bridge status
    b_res = await db.execute(select(BridgeDevice).where(BridgeDevice.user_id==user.id))
    bridges = b_res.scalars().all()
    def _aware(dt):
        if dt is None: return None
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
    connected = any(b.status=="online" and _aware(b.last_heartbeat_at) and (now - _aware(b.last_heartbeat_at)).total_seconds() < 75 for b in bridges)
    # recent commands
    c_res = await db.execute(select(BridgeCommand).where(BridgeCommand.user_id==user.id).order_by(BridgeCommand.requested_at.desc()).limit(5))
    recent_commands = [{"id": c.id, "action": c.action, "status": c.status, "requested_at": c.requested_at.isoformat()} for c in c_res.scalars().all()]
    # upcoming deadlines
    up_res = await db.execute(select(Project).where(Project.user_id==user.id, Project.deadline.is_not(None), Project.deadline >= now).order_by(Project.deadline.asc()).limit(5))
    upcoming = [{"title": p.title, "date": p.deadline.isoformat(), "slug": p.slug} for p in up_res.scalars().all()]
    # also task reminders due soon
    r_res = await db.execute(select(Task).where(Task.user_id==user.id, Task.due_date.is_not(None), Task.due_date >= now, Task.due_date < now + timedelta(days=3)).order_by(Task.due_date.asc()).limit(5))
    reminders = [{"title": t.title, "due_date": t.due_date.isoformat(), "id": t.id} for t in r_res.scalars().all()]

    return {
        "today_tasks": today_count,
        "overdue_tasks": overdue_count,
        "active_projects": active_count,
        "recent_notes": recent_notes,
        "bridge_status": "online" if connected else "offline",
        "bridge_devices": [{"id": b.id, "name": b.name, "status": b.status, "last_heartbeat_at": (_aware(b.last_heartbeat_at).isoformat() if b.last_heartbeat_at else None)} for b in bridges],
        "recent_commands": recent_commands,
        "upcoming_deadlines": upcoming,
        "reminders": reminders,
    }

@router.get("/layouts")
async def layouts(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models.dashboard import DashboardLayout
    res = await db.execute(select(DashboardLayout).where(DashboardLayout.user_id==user.id))
    layouts = res.scalars().all()
    return {"data": [{"id": l.id, "name": l.name, "device_type": l.device_type, "is_default": l.is_default} for l in layouts]}

@router.post("/layouts")
async def create_layout(payload: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models.dashboard import DashboardLayout, DashboardWidget
    import uuid
    lay = DashboardLayout(id=str(uuid.uuid4()), user_id=user.id, name=payload.get("name","Default"), device_type=payload.get("device_type","desktop"), is_default=payload.get("is_default", False))
    db.add(lay)
    await db.commit()
    await db.refresh(lay)
    return {"id": lay.id, "name": lay.name}
