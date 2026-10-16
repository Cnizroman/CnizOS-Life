import pytest, asyncio, os
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.db.session import Base, get_db
from app.main import app

TEST_DB = "sqlite+aiosqlite:///./test_cnizos.db"

@pytest.fixture(autouse=False)
async def client():
    # ensure clean db
    if os.path.exists("./test_cnizos.db"):
        try:
            os.remove("./test_cnizos.db")
        except: pass
    eng = create_async_engine(TEST_DB, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    SessionLocal = async_sessionmaker(eng, expire_on_commit=False)
    async def override_get_db():
        async with SessionLocal() as session:
            yield session
    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await eng.dispose()
    if os.path.exists("./test_cnizos.db"):
        try:
            os.remove("./test_cnizos.db")
        except: pass
