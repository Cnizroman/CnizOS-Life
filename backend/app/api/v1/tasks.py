from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime, timezone, timedelta
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.task import Task, TaskReminder
from app.models.activity import ActivityLog
from app.schemas.task import TaskCreate, TaskUpdate, TaskOut

router = APIRouter(prefix="/tasks", tags=["tasks"])

@router.get("", response_model=dict)
async def list_tasks(
    q: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    project_id: str | None = None,
    view: str | None = None,  # today,overdue,upcoming,done
    overdue: bool | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Task).where(Task.user_id == user.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Task.title.ilike(like), Task.description.ilike(like)))
    if status:
        stmt = stmt.where(Task.status == status)
    if priority:
        stmt = stmt.where(Task.priority == priority)
    if project_id:
        stmt = stmt.where(Task.project_id == project_id)
    now = datetime.now(tz=timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    today_end = today_start + timedelta(days=1)
    if view == "today":
        stmt = stmt.where(Task.due_date >= today_start, Task.due_date < today_end)
    elif view == "overdue":
        stmt = stmt.where(Task.due_date < now, Task.status != "done", Task.status != "cancelled")
    elif view == "upcoming":
        stmt = stmt.where(Task.due_date >= now, Task.due_date < now + timedelta(days=7))
    elif view == "done":
        stmt = stmt.where(Task.status == "done")
    if overdue:
        stmt = stmt.where(Task.due_date < now, Task.status != "done")

    stmt = stmt.order_by(Task.due_date.is_(None), Task.due_date.asc(), Task.created_at.desc()).offset((page-1)*limit).limit(limit)
    res = await db.execute(stmt)
    items = res.scalars().all()
    # total
    cnt = await db.execute(select(Task).where(Task.user_id == user.id))
    total = len(cnt.scalars().all())
    return {"data": [TaskOut.model_validate(t).model_dump() for t in items], "meta": {"page": page, "limit": limit, "total": total}}

@router.post("", response_model=TaskOut, status_code=201)
async def create_task(payload: TaskCreate, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    task = Task(
        user_id=user.id,
        title=payload.title,
        description=payload.description,
        status=payload.status or "todo",
        priority=payload.priority or "medium",
        project_id=payload.project_id,
        category=payload.category,
        due_date=payload.due_date,
        tags=payload.tags or [],
        recurrence_rule=payload.recurrence_rule,
    )
    db.add(task)
    await db.flush()
    db.add(ActivityLog(user_id=user.id, action="task.create", entity_type="task", entity_id=task.id, meta={"title": task.title}, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    await db.refresh(task)
    return TaskOut.model_validate(task)

@router.get("/calendar")
async def calendar(from_date: str | None = None, to: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Task).where(Task.user_id == user.id, Task.due_date.is_not(None))
    if from_date:
        try:
            fd = datetime.fromisoformat(from_date)
            stmt = stmt.where(Task.due_date >= fd)
        except: pass
    if to:
        try:
            td = datetime.fromisoformat(to)
            stmt = stmt.where(Task.due_date <= td)
        except: pass
    res = await db.execute(stmt.order_by(Task.due_date.asc()))
    items = res.scalars().all()
    return {"data": [TaskOut.model_validate(t).model_dump() for t in items]}

@router.get("/{task_id}", response_model=TaskOut)
async def get_task(task_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    t = res.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    return TaskOut.model_validate(t)

@router.patch("/{task_id}", response_model=TaskOut)
async def update_task(task_id: str, payload: TaskUpdate, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    t = res.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        setattr(t, k, v)
    if "status" in data and data["status"] == "done":
        t.completed_at = datetime.now(tz=timezone.utc)
    t.updated_at = datetime.now(tz=timezone.utc)
    db.add(ActivityLog(user_id=user.id, action="task.update", entity_type="task", entity_id=t.id, meta={"fields": list(data.keys())}, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    await db.refresh(t)
    return TaskOut.model_validate(t)

@router.delete("/{task_id}")
async def delete_task(task_id: str, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    t = res.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    await db.delete(t)
    db.add(ActivityLog(user_id=user.id, action="task.delete", entity_type="task", entity_id=task_id, meta={}, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    return {"ok": True}

@router.post("/{task_id}/reminders")
async def add_reminder(task_id: str, payload: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Task).where(Task.id == task_id, Task.user_id == user.id))
    t = res.scalar_one_or_none()
    if not t:
        raise HTTPException(status_code=404, detail="Task not found")
    remind_at = payload.get("remind_at")
    if not remind_at:
        raise HTTPException(status_code=422, detail="remind_at required")
    try:
        dt = datetime.fromisoformat(remind_at.replace("Z", "+00:00"))
    except:
        raise HTTPException(status_code=422, detail="invalid remind_at")
    r = TaskReminder(task_id=task_id, remind_at=dt, channel=payload.get("channel","in_app"))
    db.add(r)
    await db.commit()
    await db.refresh(r)
    return {"id": r.id, "remind_at": r.remind_at, "status": r.delivery_status}
