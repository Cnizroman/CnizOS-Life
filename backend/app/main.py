from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
import uuid
import json
import hashlib
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from app.core.config import get_settings
from app.db.session import engine, Base
# import all models to register tables
import app.models.user
import app.models.project
import app.models.task
import app.models.note
import app.models.creative
import app.models.dashboard
import app.models.bridge
import app.models.automation
import app.models.activity

from app.api.v1.auth import router as auth_router
from app.api.v1.health import router as health_router
from app.api.v1.dashboard import router as dash_router
from app.api.v1.projects import router as proj_router
from app.api.v1.tasks import router as tasks_router
from app.api.v1.notes import router as notes_router
from app.api.v1.search import router as search_router
from app.api.v1.creative import router as creative_router
from app.api.v1.bridge import router as bridge_router
from app.api.v1.automation import router as automation_router
from app.api.v1.zoro import router as zoro_router
from app.api.v1.devices import router as devices_router
from app.api.v1.settings import router as settings_router
from app.ws.manager import connected_bridges, connected_clients

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(title="CnizOS Backend", version="1.0.0 - Full", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response

@app.exception_handler(Exception)
async def generic_handler(request: Request, exc: Exception):
    # don't hide HTTPExceptions
    from fastapi import HTTPException
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail, "code": "HTTP_ERROR", "request_id": getattr(request.state, "request_id", None)})
    return JSONResponse(status_code=500, content={"detail": "Internal server error", "code": "INTERNAL_ERROR", "request_id": getattr(request.state, "request_id", None)})

# Routers
app.include_router(health_router)
app.include_router(auth_router, prefix="/api/v1")
app.include_router(dash_router, prefix="/api/v1")
app.include_router(proj_router, prefix="/api/v1")
app.include_router(tasks_router, prefix="/api/v1")
app.include_router(notes_router, prefix="/api/v1")
app.include_router(search_router, prefix="/api/v1")
app.include_router(creative_router, prefix="/api/v1")
app.include_router(bridge_router, prefix="/api/v1")
app.include_router(automation_router, prefix="/api/v1")
app.include_router(zoro_router, prefix="/api/v1")
app.include_router(devices_router, prefix="/api/v1")
app.include_router(settings_router, prefix="/api/v1")

# Bridge WebSocket (outbound from Bridge) — use shared manager
# connected_bridges imported from app.ws.manager

@app.websocket("/ws/bridge")
async def ws_bridge(ws: WebSocket):
    await ws.accept()
    bridge_id = None
    try:
        # expect auth message first
        data = await ws.receive_text()
        try:
            msg = json.loads(data)
        except:
            await ws.send_json({"type":"auth_error","detail":"invalid json"})
            await ws.close()
            return
        token = msg.get("token")
        if not token:
            await ws.send_json({"type":"auth_error","detail":"missing token"})
            await ws.close()
            return
        # validate token
        from sqlalchemy import select
        from app.db.session import AsyncSessionLocal
        from app.models.bridge import BridgeDevice
        async with AsyncSessionLocal() as db:
            # hash compare
            h = hashlib.sha256(token.encode()).hexdigest()
            res = await db.execute(select(BridgeDevice).where(BridgeDevice.token_hash==h))
            dev = res.scalar_one_or_none()
            if not dev:
                await ws.send_json({"type":"auth_error","code":"INVALID_TOKEN"})
                await ws.close()
                return
            bridge_id = dev.id
            dev.status = "online"
            dev.last_heartbeat_at = datetime.now(tz=timezone.utc)
            await db.commit()
            await ws.send_json({"type":"auth_ok","bridge_id": bridge_id})
            connected_bridges[bridge_id] = ws
            # forward pending commands
            from app.models.bridge import BridgeCommand
            pending = await db.execute(select(BridgeCommand).where(BridgeCommand.bridge_id==bridge_id, BridgeCommand.status=="queued"))
            for cmd in pending.scalars().all():
                await ws.send_json({"type":"command","id": cmd.id, "action": cmd.action, "params": cmd.params})

        while True:
            data = await ws.receive_text()
            msg = json.loads(data)
            t = msg.get("type")
            if t == "heartbeat":
                async with AsyncSessionLocal() as db:
                    res = await db.execute(select(BridgeDevice).where(BridgeDevice.id==bridge_id))
                    dev = res.scalar_one_or_none()
                    if dev:
                        dev.last_heartbeat_at = datetime.now(tz=timezone.utc)
                        dev.status = "online"
                        dev.system_info = msg.get("system_info")
                        await db.commit()
            elif t in ("ack","result"):
                cmd_id = msg.get("id")
                status = msg.get("status")
                async with AsyncSessionLocal() as db:
                    from sqlalchemy import select as sel
                    res = await db.execute(sel(BridgeCommand).where(BridgeCommand.id==cmd_id))
                    cmd = res.scalar_one_or_none()
                    if cmd:
                        cmd.status = status
                        if status == "running":
                            cmd.started_at = datetime.now(tz=timezone.utc)
                        elif status in ("succeeded","failed"):
                            cmd.finished_at = datetime.now(tz=timezone.utc)
                            cmd.result = msg.get("result")
                            cmd.error_code = msg.get("error_code")
                            cmd.error_message = msg.get("error_message")
                        await db.commit()
            elif t == "pong":
                pass
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"ws bridge error: {e}")
    finally:
        if bridge_id and bridge_id in connected_bridges:
            del connected_bridges[bridge_id]
        # mark offline after disconnect (optional)
        if bridge_id:
            try:
                from app.db.session import AsyncSessionLocal
                from sqlalchemy import select
                from app.models.bridge import BridgeDevice
                async with AsyncSessionLocal() as db:
                    res = await db.execute(select(BridgeDevice).where(BridgeDevice.id==bridge_id))
                    dev = res.scalar_one_or_none()
                    if dev:
                        # keep last heartbeat, status will be computed as offline after timeout
                        await db.commit()
            except: pass

# Events WebSocket for frontend (simple broadcast) — use shared manager

@app.websocket("/ws/events")
async def ws_events(ws: WebSocket):
    await ws.accept()
    connected_clients.add(ws)
    try:
        while True:
            await ws.receive_text()
    except:
        pass
    finally:
        connected_clients.discard(ws)

# Static for storage
import os
if os.path.exists("storage"):
    app.mount("/storage", StaticFiles(directory="storage"), name="storage")

@app.get("/")
async def root():
    return {"name": "CnizOS Backend", "version": "1.0.0-Full", "docs": "/docs", "health": "/health"}

@app.get("/api/health")
async def api_health():
    return {"status": "ok"}
