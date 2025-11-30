import asyncio
from sqlalchemy import text
from app.db.session import engine

async def add_columns():
    async with engine.begin() as conn:
        print("Adding 'full_name' column...")
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN full_name VARCHAR(100)"))
            print("Added 'full_name'.")
        except Exception as e:
            print(f"Skipped 'full_name': {e}")

        print("Adding 'about' column...")
        try:
            await conn.execute(text("ALTER TABLE users ADD COLUMN about VARCHAR(255)"))
            print("Added 'about'.")
        except Exception as e:
            print(f"Skipped 'about': {e}")

if __name__ == "__main__":
    asyncio.run(add_columns())
