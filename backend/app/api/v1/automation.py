import uuid
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone
from app.db.session import get_db
from app.api.v1.deps import get_current_user
from app.models.user import User
from app.models.automation import AutomationScenario, AutomationStep, AutomationRun
from app.models.activity import ActivityLog
from app.models.bridge import BridgeCommand, BridgeDevice

router = APIRouter(prefix="/automation", tags=["automation"])

@router.get("/scenarios")
async def list_scenarios(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AutomationScenario).where(AutomationScenario.user_id==user.id).order_by(AutomationScenario.created_at.desc()))
    items = res.scalars().all()
    # fetch steps
    out = []
    for s in items:
        steps_res = await db.execute(select(AutomationStep).where(AutomationStep.scenario_id==s.id).order_by(AutomationStep.position.asc()))
        steps = steps_res.scalars().all()
        out.append({"id": s.id, "name": s.name, "description": s.description, "trigger_type": s.trigger_type, "trigger_config": s.trigger_config, "is_enabled": s.is_enabled, "steps": [{"id": st.id, "action": st.action, "params": st.params, "position": st.position, "continue_on_error": st.continue_on_error} for st in steps]})
    return {"data": out}

@router.post("/scenarios")
async def create_scenario(payload: dict, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    scen = AutomationScenario(user_id=user.id, name=payload.get("name","Untitled"), description=payload.get("description"), trigger_type=payload.get("trigger_type","manual"), trigger_config=payload.get("trigger_config",{}), is_enabled=payload.get("is_enabled", True))
    db.add(scen)
    await db.flush()
    for step in payload.get("steps", []):
        st = AutomationStep(scenario_id=scen.id, position=step.get("position",0), action=step.get("action"), params=step.get("params",{}), continue_on_error=step.get("continue_on_error", False))
        db.add(st)
    db.add(ActivityLog(user_id=user.id, action="automation.create", entity_type="automation_scenario", entity_id=scen.id, meta={"name": scen.name}, request_id=request.state.request_id, ip=request.client.host if request.client else None))
    await db.commit()
    await db.refresh(scen)
    return {"id": scen.id, "name": scen.name}

@router.get("/scenarios/{sid}")
async def get_scenario(sid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AutomationScenario).where(AutomationScenario.id==sid, AutomationScenario.user_id==user.id))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found")
    steps_res = await db.execute(select(AutomationStep).where(AutomationStep.scenario_id==sid).order_by(AutomationStep.position.asc()))
    steps = steps_res.scalars().all()
    return {"id": s.id, "name": s.name, "description": s.description, "trigger_type": s.trigger_type, "trigger_config": s.trigger_config, "is_enabled": s.is_enabled, "steps": [{"id": st.id, "action": st.action, "params": st.params, "position": st.position} for st in steps]}

@router.patch("/scenarios/{sid}")
async def update_scenario(sid: str, payload: dict, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AutomationScenario).where(AutomationScenario.id==sid, AutomationScenario.user_id==user.id))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found")
    for k in ["name","description","trigger_type","trigger_config","is_enabled"]:
        if k in payload:
            setattr(s, k, payload[k])
    s.updated_at = datetime.now(tz=timezone.utc)
    if "steps" in payload:
        # replace steps
        from sqlalchemy import delete
        await db.execute(delete(AutomationStep).where(AutomationStep.scenario_id==sid))
        for step in payload["steps"]:
            st = AutomationStep(scenario_id=sid, position=step.get("position",0), action=step.get("action"), params=step.get("params",{}), continue_on_error=step.get("continue_on_error", False))
            db.add(st)
    await db.commit()
    await db.refresh(s)
    return {"id": s.id, "name": s.name}

@router.delete("/scenarios/{sid}")
async def delete_scenario(sid: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AutomationScenario).where(AutomationScenario.id==sid, AutomationScenario.user_id==user.id))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found")
    await db.delete(s)
    await db.commit()
    return {"ok": True}

@router.post("/scenarios/{sid}/run")
async def run_scenario(sid: str, request: Request, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AutomationScenario).where(AutomationScenario.id==sid, AutomationScenario.user_id==user.id))
    s = res.scalar_one_or_none()
    if not s:
        raise HTTPException(status_code=404, detail="Scenario not found")
    if not s.is_enabled:
        raise HTTPException(status_code=400, detail="Scenario disabled")
    steps_res = await db.execute(select(AutomationStep).where(AutomationStep.scenario_id==sid).order_by(AutomationStep.position.asc()))
    steps = steps_res.scalars().all()
    run = AutomationRun(scenario_id=sid, status="running")
    db.add(run)
    await db.flush()
    step_results = []
    failed = False
    error_msg = None
    # Mock execution sequentially via Bridge commands (if bridge available)
    # For now simulate: try to create bridge commands, if fails mark failed
    for st in steps:
        try:
            # validate action exists
            allowed = ["app.launch","folder.open","project.open","system.volume.set","system.volume.get","system.status.get","profile.activate"]
            if st.action not in allowed:
                raise ValueError(f"Unknown action {st.action}")
            # simulate success
            step_results.append({"step_id": st.id, "action": st.action, "status":"succeeded", "result": {"mock": True}})
        except Exception as e:
            step_results.append({"step_id": st.id, "action": st.action, "status":"failed", "error": str(e)})
            if not st.continue_on_error:
                failed = True
                error_msg = str(e)
                break
    run.step_results = step_results
    run.status = "failed" if failed else "succeeded"
    run.error = error_msg
    run.finished_at = datetime.now(tz=timezone.utc)
    await db.commit()
    await db.refresh(run)
    return {"run_id": run.id, "status": run.status, "step_results": step_results}

@router.get("/runs")
async def list_runs(scenario_id: str | None = None, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    # ensure scenario belongs to user
    stmt = select(AutomationRun)
    if scenario_id:
        res = await db.execute(select(AutomationScenario).where(AutomationScenario.id==scenario_id, AutomationScenario.user_id==user.id))
        if not res.scalar_one_or_none():
            raise HTTPException(status_code=404, detail="Scenario not found")
        stmt = stmt.where(AutomationRun.scenario_id==scenario_id)
    else:
        # filter by user's scenarios
        sub = select(AutomationScenario.id).where(AutomationScenario.user_id==user.id)
        res_s = await db.execute(sub)
        ids = [r for r in res_s.scalars().all()]
        if not ids:
            return {"data": []}
        stmt = stmt.where(AutomationRun.scenario_id.in_(ids))
    stmt = stmt.order_by(AutomationRun.started_at.desc()).limit(20)
    res = await db.execute(stmt)
    runs = res.scalars().all()
    return {"data": [{"id": r.id, "scenario_id": r.scenario_id, "status": r.status, "started_at": r.started_at.isoformat(), "finished_at": r.finished_at.isoformat() if r.finished_at else None, "error": r.error, "step_results": r.step_results} for r in runs]}

@router.get("/runs/{run_id}")
async def get_run(run_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AutomationRun).where(AutomationRun.id==run_id))
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
    # check ownership
    sc_res = await db.execute(select(AutomationScenario).where(AutomationScenario.id==r.scenario_id, AutomationScenario.user_id==user.id))
    if not sc_res.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Run not found")
    return {"id": r.id, "scenario_id": r.scenario_id, "status": r.status, "step_results": r.step_results, "error": r.error}

@router.post("/runs/{run_id}/cancel")
async def cancel_run(run_id: str, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(AutomationRun).where(AutomationRun.id==run_id))
    r = res.scalar_one_or_none()
    if not r:
        raise HTTPException(status_code=404, detail="Run not found")
    if r.status == "running":
        r.status = "cancelled"
        r.finished_at = datetime.now(tz=timezone.utc)
        await db.commit()
    return {"id": r.id, "status": r.status}
