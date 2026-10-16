import pytest

async def _get_token(client):
    # ensure user exists
    await client.post("/api/v1/auth/setup", json={"email":"test@cnizos.test","password":"StrongPass123"})
    r = await client.post("/api/v1/auth/login", json={"email":"test@cnizos.test","password":"StrongPass123"})
    return r.json()["access_token"]

@pytest.mark.asyncio
async def test_crud_task(client):
    token = await _get_token(client)
    h = {"Authorization": f"Bearer {token}"}
    # create
    r = await client.post("/api/v1/tasks", json={"title":"Test Task","priority":"high","due_date":"2026-10-20T10:00:00Z"}, headers=h)
    assert r.status_code==201
    task_id = r.json()["id"]
    # list
    r = await client.get("/api/v1/tasks", headers=h)
    assert r.status_code==200
    assert any(t["id"]==task_id for t in r.json()["data"])
    # update
    r = await client.patch(f"/api/v1/tasks/{task_id}", json={"status":"done"}, headers=h)
    assert r.status_code==200
    assert r.json()["status"]=="done"
    # delete
    r = await client.delete(f"/api/v1/tasks/{task_id}", headers=h)
    assert r.status_code==200

@pytest.mark.asyncio
async def test_task_auth_required(client):
    r = await client.get("/api/v1/tasks")
    assert r.status_code==401
