import asyncio
import aiomysql
import sys
import os
from sqlalchemy import text

# Add current directory to path
sys.path.append(os.getcwd())

from app.db.session import engine

async def migrate():
    print("Connecting to old DB (whatsapp_clone_db)...")
    try:
        old_conn = await aiomysql.connect(host='localhost', port=3306,
                                          user='root', password='', db='whatsapp_clone_db')
        old_cursor = await old_conn.cursor()
        await old_cursor.execute("SELECT id, username, password_hash, created_at FROM users")
        old_users = await old_cursor.fetchall()
        await old_cursor.close()
        old_conn.close()
        print(f"Found {len(old_users)} users in old DB.")
    except Exception as e:
        print(f"Error connecting to old DB: {e}")
        return

    print("Migrating to new DB (whatsap)...")
    async with engine.begin() as conn:
        for user in old_users:
            uid, username, pwd_hash, created_at = user
            print(f"Migrating user: {username}")
            
            # Check if exists
            result = await conn.execute(text("SELECT id FROM users WHERE username = :u"), {"u": username})
            existing = result.first()
            
            if existing:
                print(f"  User {username} already exists. Skipping.")
            else:
                # Insert
                # Note: we preserve ID if possible, but auto-increment might conflict if we mix.
                # Let's try to preserve ID to keep relationships if we migrate messages later.
                # But if ID 1 exists and is different, we have a problem.
                # Since new DB is empty, we can force ID.
                
                # We need to handle created_at. It might be datetime or string.
                
                await conn.execute(
                    text("INSERT INTO users (id, username, password_hash, created_at) VALUES (:id, :u, :p, :c)"),
                    {"id": uid, "u": username, "p": pwd_hash, "c": created_at}
                )
                print(f"  User {username} migrated.")

    print("Migration complete.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(migrate())
