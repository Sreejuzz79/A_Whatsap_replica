import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.user import User

async def list_users():
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User))
        users = result.scalars().all()
        for u in users:
            print(f"ID: {u.id}, Username: {u.username}, Name: {u.full_name}, Avatar Len: {len(u.avatar) if u.avatar else 0}")

if __name__ == "__main__":
    asyncio.run(list_users())
