import pytest

async def _get_token(client):
    await client.post("/api/v1/auth/setup", json={"email":"test@cnizos.test","password":"StrongPass123"})
    r = await client.post("/api/v1/auth/login", json={"email":"test@cnizos.test","password":"StrongPass123"})
    return r.json()["access_token"]

@pytest.mark.asyncio
async def test_notes_and_search(client):
    token = await _get_token(client)
    h = {"Authorization": f"Bearer {token}"}
    # create note
    r = await client.post("/api/v1/notes", json={"title":"My Idea about music","body":"music generation with AI","type":"idea"}, headers=h)
    assert r.status_code==201
    nid = r.json()["id"]
    # search global
    r = await client.get("/api/v1/search?q=music", headers=h)
    assert r.status_code==200
    assert any(x["id"]==nid for x in r.json()["results"])
    # list notes
    r = await client.get("/api/v1/notes?q=music", headers=h)
    assert r.status_code==200
    assert r.json()["data"]
    # update
    r = await client.patch(f"/api/v1/notes/{nid}", json={"title":"Updated title"}, headers=h)
    assert r.status_code==200
    assert r.json()["title"]=="Updated title"
    # archive
    r = await client.delete(f"/api/v1/notes/{nid}", headers=h)
    assert r.status_code==200

@pytest.mark.asyncio
async def test_project_note_link(client):
    token = await _get_token(client)
    h = {"Authorization": f"Bearer {token}"}
    # project
    r = await client.post("/api/v1/projects", json={"title":"LinkTest","category":"app"}, headers=h)
    pid = r.json()["id"]
    # note linked
    r = await client.post("/api/v1/notes", json={"title":"Bug report","body":"bug","type":"bug","project_ids":[pid]}, headers=h)
    nid = r.json()["id"]
    # check project notes
    r = await client.get(f"/api/v1/projects/{pid}/notes", headers=h)
    assert r.status_code==200
    assert any(n["id"]==nid for n in r.json()["data"])
