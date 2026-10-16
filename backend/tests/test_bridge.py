import pytest

async def _get_token(client):
    await client.post("/api/v1/auth/setup", json={"email":"test@cnizos.test","password":"StrongPass123"})
    r = await client.post("/api/v1/auth/login", json={"email":"test@cnizos.test","password":"StrongPass123"})
    return r.json()["access_token"]

@pytest.mark.asyncio
async def test_bridge_allowlist(client):
    token = await _get_token(client)
    h = {"Authorization": f"Bearer {token}"}
    # register bridge
    r = await client.post("/api/v1/bridge/devices", json={"name":"Test PC","allowed_apps":[{"id":"vscode","label":"VS Code","exec":"C:\\Code.exe"}],"allowed_directories":["C:\\Projects"]}, headers=h)
    assert r.status_code==200
    bid = r.json()["id"]
    # allowed command
    r = await client.post("/api/v1/bridge/commands", json={"bridge_id": bid, "action":"app.launch","params":{"app_id":"vscode"}}, headers=h)
    assert r.status_code==200
    assert r.json()["status"] in ("queued","succeeded")
    # disallowed app
    r = await client.post("/api/v1/bridge/commands", json={"bridge_id": bid, "action":"app.launch","params":{"app_id":"evil"}}, headers=h)
    assert r.status_code==200
    assert r.json()["status"]=="failed"
    # disallowed path
    r = await client.post("/api/v1/bridge/commands", json={"bridge_id": bid, "action":"folder.open","params":{"path":"C:\\Windows\\System32"}}, headers=h)
    assert r.status_code==200
    assert r.json()["status"]=="failed"
    # idempotency
    r1 = await client.post("/api/v1/bridge/commands", json={"bridge_id": bid, "action":"system.volume.get","params":{},"idempotency_key":"test-key-123"}, headers=h)
    r2 = await client.post("/api/v1/bridge/commands", json={"bridge_id": bid, "action":"system.volume.get","params":{},"idempotency_key":"test-key-123"}, headers=h)
    assert r1.json()["command_id"]==r2.json()["command_id"]
