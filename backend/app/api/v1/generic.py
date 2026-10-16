from fastapi import APIRouter, Depends
from app.api.v1.deps import get_current_user
from app.models.user import User

# Generic stubs for Stage 2 — will be replaced in Stage 3 with real models
router_tasks = APIRouter(prefix="/tasks", tags=["tasks"])
@router_tasks.get("")
async def list_tasks(user: User = Depends(get_current_user)):
    return {"data": [], "meta": {"total":0}}

router_notes = APIRouter(prefix="/notes", tags=["notes"])
@router_notes.get("")
async def list_notes(user: User = Depends(get_current_user)):
    return {"data": [], "meta": {"total":0}}

router_search = APIRouter(prefix="/search", tags=["search"])
@router_search.get("")
async def search(q: str = "", user: User = Depends(get_current_user)):
    return {"query": q, "results": []}

router_creative = APIRouter(prefix="/creative", tags=["creative"])
@router_creative.get("/assets")
async def creative_assets(user: User = Depends(get_current_user)):
    return {"data": []}

router_automation = APIRouter(prefix="/automation", tags=["automation"])
@router_automation.get("/scenarios")
async def scenarios(user: User = Depends(get_current_user)):
    return {"data": []}
