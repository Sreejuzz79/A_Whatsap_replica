import asyncio
import sys
import os
import sqlite3
from sqlalchemy import text

# Add current directory to path
sys.path.append(os.getcwd())

from app.db.session import engine

async def check_mysql_users():
    print("\n--- MySQL Users ---")
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT id, username, password_hash FROM users"))
            rows = result.fetchall()
            if not rows:
                print("No users found in MySQL.")
            for row in rows:
                print(f"ID: {row.id}, Username: {row.username}, Hash: {row.password_hash[:10]}...")
    except Exception as e:
        print(f"Error checking MySQL: {e}")
    finally:
        await engine.dispose()

def check_sqlite_users():
    print("\n--- SQLite Users (test.db) ---")
    db_path = "test.db"
    if not os.path.exists(db_path):
        print(f"{db_path} not found.")
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM users")
        rows = cursor.fetchall()
        if not rows:
            print("No users found in SQLite.")
        for row in rows:
            print(f"ID: {row[0]}, Username: {row[1]}, Hash: {row[2][:10]}...")
        conn.close()
    except Exception as e:
        print(f"Error checking SQLite: {e}")

async def main():
    await check_mysql_users()
    check_sqlite_users()

if __name__ == "__main__":
    asyncio.run(main())
