# app/db/session.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.config import settings
from typing import AsyncGenerator

if not settings.DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in settings or .env")

engine = create_async_engine(settings.DATABASE_URL, echo=False)

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
