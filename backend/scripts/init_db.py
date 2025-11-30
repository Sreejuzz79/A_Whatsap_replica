# scripts/init_db.py
import asyncio
from pathlib import Path
import sys
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

async def main():
    # import config/engine
    from app.db.session import engine
    # import models so they register with Base.metadata
    import app.models.user
    import app.models.message   # if you have it
    from app.models.base import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ DB tables created")

if __name__ == "__main__":
    asyncio.run(main())
