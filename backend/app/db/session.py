from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
import os
from app.core.config import get_settings

settings = get_settings()

# Support both postgres and sqlite
db_url = os.getenv("DATABASE_URL", settings.DATABASE_URL)
# For sandbox without postgres, fallback to sqlite if pg not available
# If url contains postgres but we are in sandbox without pg, we can still try sqlite
engine = create_async_engine(db_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
