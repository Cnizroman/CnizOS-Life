import pytest

@pytest.mark.asyncio
async def test_setup_and_login(client):
    # setup first user
    r = await client.post("/api/v1/auth/setup", json={"email":"test@cnizos.test","password":"StrongPass123","display_name":"Tester"})
    assert r.status_code in (200,201,403)  # if already exists, 403
    if r.status_code in (200,201):
        data = r.json()
        assert "access_token" in data
    # login
    r2 = await client.post("/api/v1/auth/login", json={"email":"test@cnizos.test","password":"StrongPass123"})
    assert r2.status_code==200
    assert "access_token" in r2.json()
    # me
    token = r2.json()["access_token"]
    r3 = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r3.status_code==200
    assert r3.json()["email"]=="test@cnizos.test"

@pytest.mark.asyncio
async def test_setup_closed(client):
    # first setup
    r1 = await client.post("/api/v1/auth/setup", json={"email":"test@cnizos.test","password":"StrongPass123"})
    assert r1.status_code in (200,201)
    # second setup should be closed
    r = await client.post("/api/v1/auth/setup", json={"email":"another@cnizos.test","password":"Pass12345"})
    assert r.status_code==403
