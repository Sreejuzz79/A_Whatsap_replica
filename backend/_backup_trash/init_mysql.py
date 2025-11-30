import asyncio
import aiomysql
import sys
import os

# Add current directory to path
sys.path.append(os.getcwd())

from app.config import settings
from app.models.base import Base
# Import models to register them
from app.models.user import User
# Message model might not exist or be imported, let's try to import it if it exists
try:
    from app.models.message import Message
except ImportError:
    print("Message model not found, skipping...")

async def init_db():
    print("Connecting to MySQL to check database...")
    try:
        # Connect to default 'mysql' database to create our db
        conn = await aiomysql.connect(host='localhost', port=3306,
                                      user='root', password='', db='mysql')
        cursor = await conn.cursor()
        await cursor.execute("CREATE DATABASE IF NOT EXISTS whatsap")
        print("Database 'whatsap' ensured.")
        await cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error creating database: {e}")
        return

    print("Creating tables...")
    try:
        # Now use SQLAlchemy engine
        from app.db.session import engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("Tables created successfully!")
        await engine.dispose()
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    asyncio.run(init_db())
