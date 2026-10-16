from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from datetime import datetime, timezone
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.note import Note, Tag, NoteTag, ProjectNote
from app.models.activity import ActivityLog
from app.schemas.note import NoteCreate, NoteUpdate, NoteOut

router = APIRouter(prefix="/notes", tags=["notes"])

@router.get("", response_model=dict)
async def list_notes(
    q: str | None = None,
    type: str | None = Query(None, alias="type"),
    collection: str | None = None,
    is_pinned: bool | None = None,
    is_favorite: bool | None = None,
    is_archived: bool | None = None,
    tag: str | None = None,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Note).where(Note.user_id == user.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where(or_(Note.title.ilike(like), Note.body.ilike(like)))
    if type:
        stmt = stmt.where(Note.type == type)
    if collection:
        stmt = stmt.where(Note.collection == collection)
    if is_pinned is not None:
        stmt = stmt.where(Note.is_pinned == is_pinned)
    if is_favorite is not None:
        stmt = stmt.where(Note.is_favorite == is_favorite)
    if is_archived is not None:
        stmt = stmt.where(Note.is_archived == is_archived)
    else:
        stmt = stmt.where(Note.is_archived == False)
    stmt = stmt.order_by(Note.is_pinned.desc(), Note.updated_at.desc()).offset((page-1)*limit).limit(limit)
    res = await db.execute(stmt)
    items = res.scalars().all()
    total_res = await db.execute(select(Note).where(Note.user_id == user.id, Note.is_archived == False))
    total = len(total_res.scalars().all())
    return {"data": [NoteOut.model_validate(n).model_dump() for n in items], "meta": {"page": page, "limit": limit, "total": total}}

@router.post("", response_model=NoteOut, status_code=201)
async def create_note(payload: NoteCreate, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    note = Note(
        user_id=user.id,
        title=payload.title,
        body=payload.body or "",
        type=payload.type or "note",
        collection=payload.collection,
        is_pinned=payload.is_pinned or False,
        is_favorite=payload.is_favorite or False,
    )
    db.add(note)
    await db.flush()
    # tags
    for tid in payload.tag_ids or []:
        db.add(NoteTag(note_id=note.id, tag_id=tid))
    for pid in payload.project_ids or []:
        db.add(ProjectNote(project_id=pid, note_id=note.id))
    db.add(ActivityLog(user_id=user.id, action="note.create", entity_type="note", entity_id=note.id, meta={"title": note.title}, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    await db.refresh(note)
    return NoteOut.model_validate(note)

@router.get("/{note_id}", response_model=NoteOut)
async def get_note(note_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Note).where(Note.id == note_id, Note.user_id == user.id))
    n = res.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Note not found")
    return NoteOut.model_validate(n)

@router.patch("/{note_id}", response_model=NoteOut)
async def update_note(note_id: str, payload: NoteUpdate, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Note).where(Note.id == note_id, Note.user_id == user.id))
    n = res.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Note not found")
    data = payload.model_dump(exclude_unset=True)
    tag_ids = data.pop("tag_ids", None)
    project_ids = data.pop("project_ids", None)
    for k, v in data.items():
        setattr(n, k, v)
    n.updated_at = datetime.now(tz=timezone.utc)
    # update tags if provided
    if tag_ids is not None:
        await db.execute(select(NoteTag).where(NoteTag.note_id == note_id))
        # delete existing
        from sqlalchemy import delete
        await db.execute(delete(NoteTag).where(NoteTag.note_id == note_id))
        for tid in tag_ids:
            db.add(NoteTag(note_id=note_id, tag_id=tid))
    if project_ids is not None:
        from sqlalchemy import delete
        await db.execute(delete(ProjectNote).where(ProjectNote.note_id == note_id))
        for pid in project_ids:
            db.add(ProjectNote(project_id=pid, note_id=note_id))
    db.add(ActivityLog(user_id=user.id, action="note.update", entity_type="note", entity_id=n.id, meta={"fields": list(data.keys())}, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    await db.refresh(n)
    return NoteOut.model_validate(n)

@router.delete("/{note_id}")
async def delete_note(note_id: str, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Note).where(Note.id == note_id, Note.user_id == user.id))
    n = res.scalar_one_or_none()
    if not n:
        raise HTTPException(status_code=404, detail="Note not found")
    n.is_archived = True
    db.add(ActivityLog(user_id=user.id, action="note.archive", entity_type="note", entity_id=note_id, meta={}, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    return {"ok": True}

@router.get("/{note_id}/history")
async def note_history(note_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    from app.models.activity import ActivityLog
    res = await db.execute(select(ActivityLog).where(ActivityLog.entity_id == note_id, ActivityLog.user_id == user.id).order_by(ActivityLog.created_at.desc()).limit(20))
    logs = res.scalars().all()
    return {"data": [{"action": l.action, "meta": l.meta, "created_at": l.created_at} for l in logs]}
