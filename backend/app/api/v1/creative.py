import uuid, os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.creative import Asset

router = APIRouter(prefix="/creative", tags=["creative"])

@router.get("/assets")
async def list_assets(
    q: str | None = None,
    type: str | None = None,
    collection: str | None = None,
    project_id: str | None = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(Asset).where(Asset.user_id == user.id)
    if q:
        like = f"%{q}%"
        stmt = stmt.where((Asset.title.ilike(like)) | (Asset.description.ilike(like)))
    if type:
        stmt = stmt.where(Asset.type == type)
    if collection:
        stmt = stmt.where(Asset.collection == collection)
    if project_id:
        stmt = stmt.where(Asset.project_id == project_id)
    stmt = stmt.order_by(Asset.created_at.desc()).limit(50)
    res = await db.execute(stmt)
    items = res.scalars().all()
    return {"data": [{"id": a.id, "title": a.title, "description": a.description, "type": a.type, "collection": a.collection, "project_id": a.project_id, "external_url": a.external_url, "storage_key": a.storage_key, "created_at": a.created_at.isoformat()} for a in items]}

@router.post("/assets")
async def create_asset(payload: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    asset = Asset(
        user_id=user.id,
        title=payload.get("title","Untitled"),
        description=payload.get("description"),
        type=payload.get("type","other"),
        collection=payload.get("collection"),
        project_id=payload.get("project_id"),
        external_url=payload.get("external_url"),
        tags=payload.get("tags",[]),
    )
    db.add(asset)
    await db.commit()
    await db.refresh(asset)
    return {"id": asset.id, "title": asset.title}

@router.get("/assets/{asset_id}")
async def get_asset(asset_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Asset).where(Asset.id==asset_id, Asset.user_id==user.id))
    a = res.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")
    return {"id": a.id, "title": a.title, "description": a.description, "type": a.type, "collection": a.collection, "external_url": a.external_url, "storage_key": a.storage_key}

@router.patch("/assets/{asset_id}")
async def update_asset(asset_id: str, payload: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Asset).where(Asset.id==asset_id, Asset.user_id==user.id))
    a = res.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")
    for k,v in payload.items():
        if hasattr(a, k):
            setattr(a, k, v)
    a.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(a)
    return {"id": a.id}

@router.delete("/assets/{asset_id}")
async def delete_asset(asset_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Asset).where(Asset.id==asset_id, Asset.user_id==user.id))
    a = res.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")
    await db.delete(a)
    await db.commit()
    return {"ok": True}

@router.post("/assets/{asset_id}/upload")
async def upload_file(asset_id: str, file: UploadFile = File(...), user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Asset).where(Asset.id==asset_id, Asset.user_id==user.id))
    a = res.scalar_one_or_none()
    if not a:
        raise HTTPException(status_code=404, detail="Asset not found")
    storage_dir = f"storage/creative/{asset_id}"
    os.makedirs(storage_dir, exist_ok=True)
    path = f"{storage_dir}/{file.filename}"
    content = await file.read()
    if len(content) > 100*1024*1024:
        raise HTTPException(status_code=413, detail="File too large (max 100MB)")
    with open(path, "wb") as f:
        f.write(content)
    a.storage_key = path
    await db.commit()
    return {"storage_key": path, "size": len(content)}
