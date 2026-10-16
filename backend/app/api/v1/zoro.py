from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.task import Task
from app.models.note import Note
from app.models.project import Project
from app.models.activity import ActivityLog

router = APIRouter(prefix="/zoro", tags=["zoro"])

# Zoro uses same Bearer token as user for now (scope check simplified)
# In prod, separate zoro_token with scope validation

@router.get("/tasks")
async def zoro_tasks(view: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from datetime import datetime, timezone, timedelta
    stmt = select(Task).where(Task.user_id==user.id)
    now = datetime.now(tz=timezone.utc)
    if view == "today":
        start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = start + timedelta(days=1)
        stmt = stmt.where(Task.due_date >= start, Task.due_date < end)
    elif view == "overdue":
        stmt = stmt.where(Task.due_date < now, Task.status.notin_(["done","cancelled"]))
    res = await db.execute(stmt.order_by(Task.due_date.asc().nulls_last()).limit(20))
    items = res.scalars().all()
    return {"data": [{"id": t.id, "title": t.title, "status": t.status, "due_date": t.due_date.isoformat() if t.due_date else None} for t in items]}

@router.post("/tasks")
async def zoro_create_task(payload: dict, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from datetime import datetime
    from app.models.task import Task
    title = payload.get("title")
    if not title:
        raise HTTPException(status_code=422, detail="title required")
    due = payload.get("due_date")
    due_dt = None
    if due:
        try:
            due_dt = datetime.fromisoformat(due.replace("Z","+00:00"))
        except:
            pass
    t = Task(user_id=user.id, title=title, description=payload.get("description"), due_date=due_dt, priority=payload.get("priority","medium"), status="todo")
    db.add(t)
    await db.flush()
    db.add(ActivityLog(user_id=user.id, action="zoro.task.create", entity_type="task", entity_id=t.id, meta={"title": title}, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    await db.refresh(t)
    return {"id": t.id, "title": t.title}

@router.patch("/tasks/{task_id}")
async def zoro_update_task(task_id: str, payload: dict, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Task).where(Task.id==task_id, Task.user_id==user.id))
    t = res.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    for k,v in payload.items():
        if hasattr(t, k):
            setattr(t, k, v)
    await db.commit()
    return {"id": t.id, "status": t.status}

@router.get("/notes/search")
async def zoro_search_notes(q: str, limit: int = 5, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    like = f"%{q}%"
    res = await db.execute(select(Note).where(Note.user_id==user.id, or_(Note.title.ilike(like), Note.body.ilike(like))).limit(limit))
    items = res.scalars().all()
    return {"data": [{"id": n.id, "title": n.title, "snippet": n.body[:120]} for n in items]}

@router.post("/notes")
async def zoro_create_note(payload: dict, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    title = payload.get("title","Untitled")
    body = payload.get("body", payload.get("title",""))
    n = Note(user_id=user.id, title=title, body=body, type=payload.get("type","note"))
    db.add(n)
    await db.flush()
    db.add(ActivityLog(user_id=user.id, action="zoro.note.create", entity_type="note", entity_id=n.id, meta={"title": title}, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    await db.refresh(n)
    return {"id": n.id, "title": n.title}

@router.get("/projects")
async def zoro_projects(q: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Project).where(Project.user_id==user.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Project.title.ilike(like), Project.description.ilike(like)))
    res = await db.execute(stmt.limit(10))
    items = res.scalars().all()
    return {"data": [{"id": p.id, "title": p.title, "slug": p.slug, "status": p.status} for p in items]}

@router.get("/projects/{pid}")
async def zoro_get_project(pid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Project).where(Project.id==pid, Project.user_id==user.id))
    p = res.scalar_one_or_none()
    if not p:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"id": p.id, "title": p.title, "description": p.description, "status": p.status, "local_path": p.local_path}

@router.post("/actions/execute")
async def zoro_execute(payload: dict, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # proxy to bridge command creation
    from app.models.bridge import BridgeDevice, BridgeCommand
    import uuid, hashlib
    from datetime import datetime, timezone
    action = payload.get("action")
    params = payload.get("params",{})
    # find first online bridge or any
    res = await db.execute(select(BridgeDevice).where(BridgeDevice.user_id==user.id).limit(1))
    dev = res.scalar_one_or_none()
    if not dev:
        raise HTTPException(status_code=502, detail="No bridge registered")
    # create command as in bridge API
    cmd = BridgeCommand(id=str(uuid.uuid4()), bridge_id=dev.id, user_id=user.id, action=action, params=params, params_safe=params, status="succeeded", result={"mock": True, "via":"zoro"}, requested_at=datetime.now(tz=timezone.utc), started_at=datetime.now(tz=timezone.utc), finished_at=datetime.now(tz=timezone.utc), idempotency_key=str(uuid.uuid4()))
    db.add(cmd)
    await db.commit()
    return {"command_id": cmd.id, "status": cmd.status, "result": cmd.result}

@router.get("/bridge/status")
async def zoro_bridge_status(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models.bridge import BridgeDevice
    res = await db.execute(select(BridgeDevice).where(BridgeDevice.user_id==user.id))
    devices = res.scalars().all()
    return {"devices": [{"id": d.id, "name": d.name, "status": d.status} for d in devices]}

@router.get("/history")
async def zoro_history(limit: int = 20, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(ActivityLog).where(ActivityLog.user_id==user.id, ActivityLog.action.like("zoro.%")).order_by(ActivityLog.created_at.desc()).limit(limit))
    logs = res.scalars().all()
    return {"data": [{"action": l.action, "meta": l.meta, "created_at": l.created_at.isoformat()} for l in logs]}
