import re
import uuid
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import datetime, timezone
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.activity import ActivityLog
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectOut

router = APIRouter(prefix="/projects", tags=["projects"])

def slugify(title: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9]+', '-', title.lower()).strip('-')
    return s or "project"

@router.get("", response_model=dict)
async def list_projects(
    q: str | None = None,
    status: str | None = None,
    category: str | None = None,
    priority: str | None = None,
    archived: bool | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Project).where(Project.user_id == user.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Project.title.ilike(like), Project.description.ilike(like)))
    if status:
        stmt = stmt.where(Project.status == status)
    if category:
        stmt = stmt.where(Project.category == category)
    if priority:
        stmt = stmt.where(Project.priority == priority)
    if archived is not None:
        if archived:
            stmt = stmt.where(Project.archived_at.is_not(None))
        else:
            stmt = stmt.where(Project.archived_at.is_(None))
    stmt = stmt.order_by(Project.updated_at.desc()).offset((page-1)*limit).limit(limit)
    res = await db.execute(stmt)
    items = res.scalars().all()
    # count total
    cnt_stmt = select(Project).where(Project.user_id == user.id)
    if q:
        like = f"%{q}%"
        cnt_stmt = cnt_stmt.where(or_(Project.title.ilike(like), Project.description.ilike(like)))
    total_res = await db.execute(cnt_stmt)
    total = len(total_res.scalars().all())
    return {"data": [ProjectOut.model_validate(p).model_dump() for p in items], "meta": {"page": page, "limit": limit, "total": total}}

@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(payload: ProjectCreate, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    base_slug = slugify(payload.title)
    slug = base_slug
    # ensure uniqueness
    for i in range(1, 100):
        res = await db.execute(select(Project).where(Project.slug == slug))
        if not res.scalar_one_or_none():
            break
        slug = f"{base_slug}-{i}"
    proj = Project(
        user_id=user.id,
        title=payload.title,
        slug=slug,
        description=payload.description,
        category=payload.category or "other",
        status=payload.status or "idea",
        priority=payload.priority or "medium",
        links=payload.links or [],
        local_path=payload.local_path,
        github_url=payload.github_url,
        demo_url=payload.demo_url,
        deadline=datetime.fromisoformat(payload.deadline) if payload.deadline else None,
    )
    db.add(proj)
    await db.flush()
    # log
    db.add(ActivityLog(user_id=user.id, action="project.create", entity_type="project", entity_id=proj.id, meta={"title": proj.title}, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    await db.refresh(proj)
    return ProjectOut.model_validate(proj)

@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # allow id or slug
    stmt = select(Project).where(Project.user_id == user.id, or_(Project.id == project_id, Project.slug == project_id))
    res = await db.execute(stmt)
    proj = res.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectOut.model_validate(proj)

@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: str, payload: ProjectUpdate, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Project).where(Project.user_id == user.id, or_(Project.id == project_id, Project.slug == project_id))
    res = await db.execute(stmt)
    proj = res.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    data = payload.model_dump(exclude_unset=True)
    for k, v in data.items():
        if k == "deadline" and v:
            try:
                v = datetime.fromisoformat(v)
            except:
                pass
        setattr(proj, k, v)
    proj.updated_at = datetime.now(tz=timezone.utc)
    db.add(ActivityLog(user_id=user.id, action="project.update", entity_type="project", entity_id=proj.id, meta={"fields": list(data.keys())}, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    await db.refresh(proj)
    return ProjectOut.model_validate(proj)

@router.delete("/{project_id}")
async def delete_project(project_id: str, hard: bool = False, request: Request = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Project).where(Project.user_id == user.id, or_(Project.id == project_id, Project.slug == project_id))
    res = await db.execute(stmt)
    proj = res.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    if hard:
        await db.delete(proj)
        action = "project.delete.hard"
    else:
        proj.archived_at = datetime.now(tz=timezone.utc)
        proj.status = "archived"
        action = "project.archive"
    db.add(ActivityLog(user_id=user.id, action=action, entity_type="project", entity_id=proj.id, meta={}, request_id=request.state.request_id if request else str(uuid.uuid4()), ip=request.client.host if request and request.client else None))
    await db.commit()
    return {"ok": True}

@router.get("/{project_id}/tasks")
async def project_tasks(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models.task import Task
    # resolve project id/slug
    stmt = select(Project).where(Project.user_id == user.id, or_(Project.id == project_id, Project.slug == project_id))
    res = await db.execute(stmt)
    proj = res.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    t_res = await db.execute(select(Task).where(Task.user_id == user.id, Task.project_id == proj.id))
    tasks = t_res.scalars().all()
    return {"data": [{"id": t.id, "title": t.title, "status": t.status, "priority": t.priority, "due_date": t.due_date} for t in tasks]}

@router.get("/{project_id}/notes")
async def project_notes(project_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models.note import Note, ProjectNote
    stmt = select(Project).where(Project.user_id == user.id, or_(Project.id == project_id, Project.slug == project_id))
    res = await db.execute(stmt)
    proj = res.scalar_one_or_none()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    pn_res = await db.execute(select(ProjectNote).where(ProjectNote.project_id == proj.id))
    pns = pn_res.scalars().all()
    note_ids = [pn.note_id for pn in pns]
    if not note_ids:
        return {"data": []}
    from sqlalchemy import select as sel
    n_res = await db.execute(sel(Note).where(Note.id.in_(note_ids)))
    notes = n_res.scalars().all()
    return {"data": [{"id": n.id, "title": n.title, "type": n.type} for n in notes]}
