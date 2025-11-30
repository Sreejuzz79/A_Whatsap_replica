# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from typing import AsyncGenerator

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in settings or .env")

# Fix for Render providing postgres:// or postgresql:// which needs to be async
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
elif db_url.startswith("postgresql://"):
    db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)

engine = create_async_engine(db_url, echo=False)

# session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

# FastAPI dependency to get DB session
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Use in route dependencies like:
        async def foo(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
