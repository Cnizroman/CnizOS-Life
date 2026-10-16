from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
import uuid
import hashlib

from app.db.session import get_db
from app.models.user import User, Session
from app.schemas.auth import SetupRequest, LoginRequest, UserOut, AuthResponse, SetupStatusOut
from app.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from app.core.config import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()

def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

@router.get("/setup-status", response_model=SetupStatusOut)
async def setup_status(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).limit(1))
    exists = res.scalar_one_or_none() is not None
    return {"setup_required": not exists}

@router.post("/setup", response_model=AuthResponse)
async def setup(payload: SetupRequest, response: Response, request: Request, db: AsyncSession = Depends(get_db)):
    # only if no users
    res = await db.execute(select(User))
    if res.scalars().first() is not None:
        raise HTTPException(status_code=403, detail="Setup already completed. Registration closed.")
    user = User(email=payload.email.lower(), password_hash=hash_password(payload.password), display_name=payload.display_name or "Owner")
    db.add(user)
    await db.flush()

    access = create_access_token(sub=user.id)
    refresh = create_refresh_token(sub=user.id)
    session = Session(
        user_id=user.id,
        refresh_token_hash=_hash_token(refresh),
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(seconds=2592000)
    )
    db.add(session)
    await db.commit()
    await db.refresh(user)

    response.set_cookie(key="refresh_token", value=refresh, httponly=True, secure=settings.COOKIE_SECURE, samesite="lax", max_age=2592000, path="/")
    return {"user": UserOut.model_validate(user), "access_token": access}

@router.post("/login", response_model=AuthResponse)
async def login(payload: LoginRequest, response: Response, request: Request, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(User).where(User.email == payload.email.lower()))
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access = create_access_token(sub=user.id)
    refresh = create_refresh_token(sub=user.id)
    session = Session(
        user_id=user.id,
        refresh_token_hash=_hash_token(refresh),
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(seconds=2592000)
    )
    db.add(session)
    await db.commit()
    response.set_cookie(key="refresh_token", value=refresh, httponly=True, secure=settings.COOKIE_SECURE, samesite="lax", max_age=2592000, path="/")
    return {"user": UserOut.model_validate(user), "access_token": access}

@router.post("/refresh")
async def refresh(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    if payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Invalid token type")
    h = _hash_token(token)
    res = await db.execute(select(Session).where(Session.refresh_token_hash == h))
    sess = res.scalar_one_or_none()
    if not sess or sess.revoked_at is not None or sess.expires_at < datetime.now(tz=timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired or revoked")
    # rotate
    sess.revoked_at = datetime.now(tz=timezone.utc)
    new_refresh = create_refresh_token(sub=payload["sub"])
    new_sess = Session(
        user_id=payload["sub"],
        refresh_token_hash=_hash_token(new_refresh),
        user_agent=request.headers.get("user-agent"),
        ip=request.client.host if request.client else None,
        expires_at=datetime.now(tz=timezone.utc) + timedelta(seconds=2592000)
    )
    db.add(new_sess)
    await db.commit()
    new_access = create_access_token(sub=payload["sub"])
    response.set_cookie(key="refresh_token", value=new_refresh, httponly=True, secure=settings.COOKIE_SECURE, samesite="lax", max_age=2592000, path="/")
    return {"access_token": new_access}

@router.post("/logout")
async def logout(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if token:
        h = _hash_token(token)
        res = await db.execute(select(Session).where(Session.refresh_token_hash == h))
        sess = res.scalar_one_or_none()
        if sess:
            sess.revoked_at = datetime.now(tz=timezone.utc)
            await db.commit()
    response.delete_cookie("refresh_token", path="/")
    return {"ok": True}

@router.get("/me", response_model=UserOut)
async def me(request: Request, db: AsyncSession = Depends(get_db)):
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    token = auth.split(" ",1)[1]
    try:
        payload = decode_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    res = await db.execute(select(User).where(User.id == payload["sub"]))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return UserOut.model_validate(user)

@router.get("/sessions")
async def list_sessions(request: Request, db: AsyncSession = Depends(get_db)):
    auth = request.headers.get("authorization")
    if not auth or not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing token")
    try:
        payload = decode_token(auth.split(" ",1)[1])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    res = await db.execute(select(Session).where(Session.user_id == payload["sub"]).order_by(Session.created_at.desc()))
    sessions = res.scalars().all()
    return {"data": [{"id": s.id, "user_agent": s.user_agent, "ip": s.ip, "created_at": s.created_at, "expires_at": s.expires_at, "revoked_at": s.revoked_at} for s in sessions]}
