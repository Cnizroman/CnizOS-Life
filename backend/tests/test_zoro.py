import pytest

async def _get_token(client):
    await client.post("/api/v1/auth/setup", json={"email":"test@cnizos.test","password":"StrongPass123"})
    r = await client.post("/api/v1/auth/login", json={"email":"test@cnizos.test","password":"StrongPass123"})
    return r.json()["access_token"]

@pytest.mark.asyncio
async def test_zoro_client(client):
    token = await _get_token(client)
    h = {"Authorization": f"Bearer {token}"}
    # create via zoro
    r = await client.post("/api/v1/zoro/tasks", json={"title":"Zoro task"}, headers=h)
    assert r.status_code==200
    tid = r.json()["id"]
    # search notes via zoro
    r = await client.post("/api/v1/zoro/notes", json={"title":"Zoro note","body":"test"}, headers=h)
    assert r.status_code==200
    nid = r.json()["id"]
    r = await client.get("/api/v1/zoro/notes/search?q=Zoro", headers=h)
    assert r.status_code==200
    assert r.json()["data"]
    # execute mock action
    r = await client.post("/api/v1/bridge/devices", json={"name":"Zoro PC"}, headers=h)
    bid = r.json()["id"]
    r = await client.post("/api/v1/zoro/actions/execute", json={"action":"system.volume.get","params":{}}, headers=h)
    assert r.status_code==200
    assert r.json()["status"]=="succeeded"
