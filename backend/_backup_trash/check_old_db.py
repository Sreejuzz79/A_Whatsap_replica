import asyncio
import aiomysql

async def check_old_db():
    print("\n--- Checking whatsapp_clone_db ---")
    try:
        conn = await aiomysql.connect(host='localhost', port=3306,
                                      user='root', password='', db='whatsapp_clone_db')
        cursor = await conn.cursor()
        await cursor.execute("SELECT id, username, password_hash FROM users")
        rows = await cursor.fetchall()
        if not rows:
            print("No users found in whatsapp_clone_db.")
        for row in rows:
            # row is tuple (id, username, hash)
            print(f"ID: {row[0]}, Username: {row[1]}, Hash: {row[2][:10]}...")
        await cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error checking whatsapp_clone_db: {e}")

if __name__ == "__main__":
    asyncio.run(check_old_db())
