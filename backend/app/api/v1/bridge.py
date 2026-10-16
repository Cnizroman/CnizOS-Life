import uuid, hashlib, json, asyncio
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone, timedelta
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.bridge import BridgeDevice, BridgeCommand, CommandPermission
from app.models.activity import ActivityLog

def _ensure_aware(dt: datetime | None):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt

router = APIRouter(prefix="/bridge", tags=["bridge"])

def hash_token(t: str) -> str:
    return hashlib.sha256(t.encode()).hexdigest()

@router.get("/status")
async def bridge_status(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BridgeDevice).where(BridgeDevice.user_id==user.id))
    devices = res.scalars().all()
    now = datetime.now(tz=timezone.utc)
    for d in devices:
        hb = _ensure_aware(d.last_heartbeat_at)
        if hb and (now - hb).total_seconds() < 75:
            d.status = "online"
        elif hb:
            d.status = "offline"
    # check connected = any online
    connected = any(d.status=="online" for d in devices)
    return {"connected": connected, "devices": [{"id": d.id, "name": d.name, "status": d.status, "last_heartbeat_at": _ensure_aware(d.last_heartbeat_at).isoformat() if d.last_heartbeat_at else None} for d in devices]}

@router.get("/devices")
async def list_devices(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BridgeDevice).where(BridgeDevice.user_id==user.id).order_by(BridgeDevice.created_at.desc()))
    items = res.scalars().all()
    return {"data": [{"id": d.id, "name": d.name, "status": d.status, "last_heartbeat_at": d.last_heartbeat_at.isoformat() if d.last_heartbeat_at else None, "allowed_apps": d.allowed_apps, "allowed_directories": d.allowed_directories, "system_info": d.system_info} for d in items]}

@router.post("/devices")
async def register_device(payload: dict, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    name = payload.get("name","Main PC")
    allowed_apps = payload.get("allowed_apps", [{"id":"vscode","label":"VS Code","exec":"C:\\Program Files\\Microsoft VS Code\\Code.exe"}])
    allowed_dirs = payload.get("allowed_directories", ["C:\\Projects","D:\\Creative"])
    token = str(uuid.uuid4())
    token_hash = hash_token(token)
    dev = BridgeDevice(user_id=user.id, name=name, token_hash=token_hash, allowed_apps=allowed_apps, allowed_directories=allowed_dirs)
    db.add(dev)
    await db.flush()
    # default permissions
    for action in ["app.launch","folder.open","project.open","system.volume.set","system.volume.get","system.status.get","profile.activate"]:
        db.add(CommandPermission(bridge_id=dev.id, action=action, is_enabled=True, requires_confirmation=False))
    db.add(ActivityLog(user_id=user.id, action="bridge.register", entity_type="bridge_device", entity_id=dev.id, meta={"name": name}, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    await db.refresh(dev)
    return {"id": dev.id, "name": dev.name, "bridge_token": token, "warning": "Сохрани токен — показывается один раз!"}

@router.get("/devices/{device_id}")
async def get_device(device_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BridgeDevice).where(BridgeDevice.id==device_id, BridgeDevice.user_id==user.id))
    d = res.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Bridge not found")
    return {"id": d.id, "name": d.name, "status": d.status, "last_heartbeat_at": d.last_heartbeat_at.isoformat() if d.last_heartbeat_at else None, "allowed_apps": d.allowed_apps, "allowed_directories": d.allowed_directories}

@router.patch("/devices/{device_id}")
async def update_device(device_id: str, payload: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BridgeDevice).where(BridgeDevice.id==device_id, BridgeDevice.user_id==user.id))
    d = res.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Bridge not found")
    if "name" in payload:
        d.name = payload["name"]
    if "allowed_apps" in payload:
        d.allowed_apps = payload["allowed_apps"]
    if "allowed_directories" in payload:
        d.allowed_directories = payload["allowed_directories"]
    d.updated_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(d)
    return {"id": d.id, "name": d.name}

@router.post("/devices/{device_id}/rotate")
async def rotate_token(device_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BridgeDevice).where(BridgeDevice.id==device_id, BridgeDevice.user_id==user.id))
    d = res.scalar_one_or_none()
    if not d:
        raise HTTPException(status_code=404, detail="Bridge not found")
    token = str(uuid.uuid4())
    d.token_hash = hash_token(token)
    await db.commit()
    return {"bridge_token": token}

@router.get("/actions")
async def actions(user: User = Depends(get_current_user)):
    return [
        {"id":"app.launch","description":"Запуск разрешённого приложения","params_schema":{"app_id":"string"},"requires_confirmation":False},
        {"id":"folder.open","description":"Открыть разрешённую папку","params_schema":{"path":"string"},"requires_confirmation":False},
        {"id":"project.open","description":"Открыть проект","params_schema":{"project_id":"string"},"requires_confirmation":False},
        {"id":"system.volume.set","description":"Установить громкость 0-100","params_schema":{"level":"integer 0-100"},"requires_confirmation":False},
        {"id":"system.volume.get","description":"Получить громкость","params_schema":{},"requires_confirmation":False},
        {"id":"system.status.get","description":"Статус системы","params_schema":{},"requires_confirmation":False},
        {"id":"profile.activate","description":"Активировать профиль","params_schema":{"profile":"string"},"requires_confirmation":False},
    ]

@router.post("/commands")
async def create_command(payload: dict, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    bridge_id = payload.get("bridge_id")
    action = payload.get("action")
    params = payload.get("params", {})
    idempotency_key = payload.get("idempotency_key") or str(uuid.uuid4())
    if not bridge_id or not action:
        raise HTTPException(status_code=422, detail="bridge_id and action required")
    # check bridge belongs to user
    res = await db.execute(select(BridgeDevice).where(BridgeDevice.id==bridge_id, BridgeDevice.user_id==user.id))
    dev = res.scalar_one_or_none()
    if not dev:
        raise HTTPException(status_code=404, detail="Bridge not found")
    # check permission
    perm_res = await db.execute(select(CommandPermission).where(CommandPermission.bridge_id==bridge_id, CommandPermission.action==action))
    perm = perm_res.scalar_one_or_none()
    if perm and not perm.is_enabled:
        raise HTTPException(status_code=403, detail=f"Action {action} disabled")
    # check if idempotency exists
    exist = await db.execute(select(BridgeCommand).where(BridgeCommand.idempotency_key==idempotency_key))
    ex = exist.scalar_one_or_none()
    if ex:
        return {"command_id": ex.id, "status": ex.status, "idempotent": True}
    # validate params against allow-list (basic)
    error = None
    if action == "app.launch":
        app_id = params.get("app_id")
        if not any(a.get("id")==app_id for a in (dev.allowed_apps or [])):
            error = f"App {app_id} not allowed"
    elif action == "folder.open":
        path = params.get("path","")
        # check prefix
        allowed = dev.allowed_directories or []
        ok = any(path.lower().startswith(d.lower()) for d in allowed)
        if not ok:
            error = f"Path {path} not in allowed_directories"
    elif action == "system.volume.set":
        lvl = params.get("level")
        if not isinstance(lvl, int) or not (0 <= lvl <= 100):
            error = "level must be int 0-100"

    cmd = BridgeCommand(
        id=str(uuid.uuid4()),
        bridge_id=bridge_id,
        user_id=user.id,
        action=action,
        params=params,
        params_safe=params,  # in real log without secrets
        status="failed" if error else "queued",
        error_code="NOT_ALLOWED" if error else None,
        error_message=error,
        idempotency_key=idempotency_key,
        requested_at=datetime.now(tz=timezone.utc),
    )
    if error:
        cmd.finished_at = datetime.now(tz=timezone.utc)
    db.add(cmd)
    db.add(ActivityLog(user_id=user.id, action=f"bridge.command.{action}", entity_type="bridge_command", entity_id=cmd.id, meta={"action": action, "params_safe": params}, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    await db.refresh(cmd)
    # Try to push via WSS if bridge online
    pushed = False
    if not error:
        try:
            from app.ws.manager import connected_bridges
            ws = connected_bridges.get(bridge_id)
            if ws:
                await ws.send_json({"type":"command","id": cmd.id, "action": action, "params": params})
                pushed = True
                # keep queued, bridge will ack
        except: pass

        # If not pushed and bridge offline, mock auto-succeed for demo
        if not pushed and not error:
            hb = _ensure_aware(dev.last_heartbeat_at)
            is_online = hb and (datetime.now(tz=timezone.utc) - hb).total_seconds() < 75
            if not is_online:
                # mock
                cmd.status = "succeeded"
                cmd.result = {"mock": True, "message": f"Mock executed {action}"}
                cmd.started_at = datetime.now(tz=timezone.utc)
                cmd.finished_at = datetime.now(tz=timezone.utc)
                await db.commit()
    return {"command_id": cmd.id, "status": cmd.status, "error": error}

@router.get("/commands")
async def list_commands(bridge_id: str | None = None, status: str | None = None, limit: int = 20, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(BridgeCommand).where(BridgeCommand.user_id==user.id).order_by(BridgeCommand.requested_at.desc()).limit(limit)
    if bridge_id:
        stmt = stmt.where(BridgeCommand.bridge_id==bridge_id)
    if status:
        stmt = stmt.where(BridgeCommand.status==status)
    res = await db.execute(stmt)
    items = res.scalars().all()
    return {"data": [{"id": c.id, "bridge_id": c.bridge_id, "action": c.action, "params": c.params, "status": c.status, "result": c.result, "error_code": c.error_code, "error_message": c.error_message, "requested_at": c.requested_at.isoformat(), "started_at": c.started_at.isoformat() if c.started_at else None, "finished_at": c.finished_at.isoformat() if c.finished_at else None} for c in items]}

@router.get("/commands/{command_id}")
async def get_command(command_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(BridgeCommand).where(BridgeCommand.id==command_id, BridgeCommand.user_id==user.id))
    c = res.scalar_one_or_none()
    if not c:
        raise HTTPException(status_code=404, detail="Command not found")
    # expire if queued >60s
    ra = _ensure_aware(c.requested_at)
    if c.status=="queued" and ra and (datetime.now(tz=timezone.utc) - ra).total_seconds() > 60:
        c.status = "expired"
        c.error_code = "TIMEOUT"
        c.error_message = "Bridge did not respond in 60s"
        await db.commit()
        await db.refresh(c)
    return {"id": c.id, "bridge_id": c.bridge_id, "action": c.action, "params": c.params, "status": c.status, "result": c.result, "error_code": c.error_code, "error_message": c.error_message, "requested_at": c.requested_at.isoformat(), "started_at": c.started_at.isoformat() if c.started_at else None, "finished_at": c.finished_at.isoformat() if c.finished_at else None}
