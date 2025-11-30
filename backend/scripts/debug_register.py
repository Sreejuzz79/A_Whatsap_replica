# scripts/debug_register.py
import asyncio
import traceback
import sys
from pathlib import Path

# ensure we run from project root so imports work
root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root))

print("PROJECT ROOT:", root)

async def main():
    try:
        # import project-specific things
        from app.config import settings
        from app.db.session import engine, AsyncSessionLocal  # adapt names if different
        from app.models.base import Base                    # adapt if your Base path differs
        from app.models.user import User
        from app.utils.security import hash_password, verify_password, create_access_token

        print("\nLoaded settings:")
        print(" DATABASE_URL =", getattr(settings, "DATABASE_URL", None))
        print(" SECRET_KEY  =", bool(getattr(settings, "SECRET_KEY", None)))

        # 1) create tables
        print("\n=== Creating DB tables (if missing) ===")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print(" Tables created / already exist.")

        # 2) test hashing & token
        print("\n=== Testing security helpers ===")
        try:
            h = hash_password("1234")
            print(" hash_password OK (len):", len(h) if h else "None")
            print(" verify_password OK:", verify_password("1234", h))
        except Exception as e:
            print(" ERROR in hash/verify:")
            traceback.print_exc()

        try:
            tok = create_access_token(1)
            print(" create_access_token OK (sample):", tok[:30] if isinstance(tok, str) else repr(tok))
        except Exception:
            print(" ERROR in create_access_token:")
            traceback.print_exc()

        # 3) attempt to create a user with AsyncSession
        print("\n=== Attempting DB user insert (simulates /auth/register) ===")
        async with AsyncSessionLocal() as session:   # adjust name if needed
            try:
                # check existing
                q = await session.execute(__import__("sqlalchemy").select(User).where(User.username == "sree_debug"))
                if q.scalars().first():
                    print(" user 'sree_debug' already exists (deleting for fresh test)...")
                    u = q.scalars().first()
                    await session.delete(u)
                    await session.commit()

                user = User(username="sree_debug", password_hash=hash_password("1234"))
                session.add(user)
                await session.commit()
                await session.refresh(user)
                print(" Insert OK: id=", getattr(user, "id", None), "username=", user.username)
            except Exception:
                print(" ERROR during DB insert:")
                traceback.print_exc()

    except Exception:
        print("Fatal error during diagnostics:")
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
