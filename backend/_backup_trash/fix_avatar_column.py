import asyncio
from sqlalchemy import text
from app.db.session import engine

async def fix_avatar_column():
    async with engine.begin() as conn:
        print("Altering users table...")
        await conn.execute(text("ALTER TABLE users MODIFY COLUMN avatar LONGTEXT;"))
        print("Done!")

if __name__ == "__main__":
    asyncio.run(fix_avatar_column())
