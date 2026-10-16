from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.project import Project
from app.models.task import Task
from app.models.note import Note

router = APIRouter(prefix="/search", tags=["search"])

@router.get("")
async def global_search(q: str = Query(..., min_length=1), types: str | None = None, limit: int = Query(20, ge=1, le=50), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    results = []
    wanted = set(types.split(",")) if types else {"projects","tasks","notes"}
    like = f"%{q}%"
    if "projects" in wanted or "project" in wanted:
        res = await db.execute(select(Project).where(Project.user_id == user.id, or_(Project.title.ilike(like), Project.description.ilike(like))).limit(limit))
        for p in res.scalars().all():
            snippet = (p.description or "")[:120]
            results.append({"type":"project","id":p.id,"title":p.title,"snippet":snippet,"url":f"/projects/{p.slug}","score":0.9})
    if "tasks" in wanted or "task" in wanted:
        res = await db.execute(select(Task).where(Task.user_id == user.id, or_(Task.title.ilike(like), Task.description.ilike(like))).limit(limit))
        for t in res.scalars().all():
            results.append({"type":"task","id":t.id,"title":t.title,"snippet":(t.description or "")[:120],"url":f"/planner?task={t.id}","score":0.8})
    if "notes" in wanted or "notes" in wanted or "note" in wanted:
        res = await db.execute(select(Note).where(Note.user_id == user.id, or_(Note.title.ilike(like), Note.body.ilike(like))).limit(limit))
        for n in res.scalars().all():
            # highlight snippet
            body = n.body[:200]
            idx = body.lower().find(q.lower())
            snippet = body[max(0, idx-40): idx+80] if idx>=0 else body[:120]
            results.append({"type":"note","id":n.id,"title":n.title,"snippet":snippet,"url":f"/memory/{n.id}","score":0.85})
    # sort by score
    results = sorted(results, key=lambda x: x["score"], reverse=True)[:limit]
    return {"query": q, "results": results}
