# debug_create_tables.py
"""
Usage:
  (.venv) python debug_create_tables.py
  (.venv) python debug_create_tables.py --models myapp.models
"""
import os
import sys
import argparse
import importlib
import asyncio
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.engine.url import make_url

# Try to import async engine tools lazily if needed
try:
    from sqlalchemy.ext.asyncio import create_async_engine
except Exception:
    create_async_engine = None

from app.models.user import User
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.call_log import CallLog
from app.db.session import engine
from app.models.base import Base

COMMON_MODEL_MODULES = [
    "models",
    "app.models",
    "myapp.models",
    "backend.models",
    "src.models",
]

parser = argparse.ArgumentParser()
parser.add_argument("--models", default=None, help="Python module path to import Base (e.g. myapp.models)")
parser.add_argument("--db-env", default=None, help="Env var name that contains DB URL (default: tries common names)")
args = parser.parse_args()

def find_db_url():
    # If user passed explicit env var name, check it
    env_names = []
    if args.db_env:
        env_names.append(args.db_env)
    # common env vars
    env_names += [
        "DATABASE_URL",
        "SQLALCHEMY_DATABASE_URL",
        "DATABASE_URI",
        "DB_URL",
    ]
    for name in env_names:
        val = os.environ.get(name)
        if val:
            return val, name
    # Try reading settings modules
    for modname in ("settings", "config", "app.settings", "app.config"):
        try:
            m = importlib.import_module(modname)
            # Check for settings object
            if hasattr(m, "settings") and hasattr(m.settings, "DATABASE_URL"):
                return m.settings.DATABASE_URL, f"{modname}.settings.DATABASE_URL"
            
            for attr in ("DATABASE_URL", "SQLALCHEMY_DATABASE_URL", "DATABASE_URI", "DB_URL"):
                val = getattr(m, attr, None)
                if val:
                    return val, f"{modname}.{attr}"
        except Exception:
            continue
    return None, None

def find_models_module():
    if args.models:
        return args.models
    for mod in COMMON_MODEL_MODULES:
        try:
            importlib.import_module(mod)
            return mod
        except Exception:
            continue
    return None

async def create_tables_async(db_url, Base):
    if create_async_engine is None:
        print("Async SQLAlchemy not available in this environment.")
        return False
    engine = create_async_engine(db_url, echo=False, future=True)
    try:
        async with engine.begin() as conn:
            print("Running Base.metadata.create_all via async connection...")
            await conn.run_sync(Base.metadata.create_all)
        print("Tables created (async).")
        await engine.dispose()
        return True
    except Exception as e:
        print("Error creating tables async:", repr(e))
        return False

def create_tables_sync(db_url, Base):
    try:
        engine = create_engine(db_url, echo=False, future=True)
        print("Running Base.metadata.create_all (sync)...")
        Base.metadata.create_all(engine)
        print("Tables created (sync).")
        return True
    except Exception as e:
        print("Error creating tables sync:", repr(e))
        return False

def list_sqlite_tables_file(db_path: Path):
    try:
        import sqlite3
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        rows = cur.fetchall()
        conn.close()
        return [r[0] for r in rows]
    except Exception as e:
        print("sqlite listing error:", repr(e))
        return None

def main():
    db_url, source = find_db_url()
    print("=== DB URL discovery ===")
    if db_url:
        print("Found DB URL from:", source)
        print("DB URL:", db_url)
    else:
        print("No DB URL found in env or common settings modules. Please set DATABASE_URL env var or pass one in settings.")
        # still continue to try to import models and create tables in default sqlite file
    models_mod = find_models_module()
    print("\n=== Models discovery ===")
    if models_mod:
        print("Found models module:", models_mod)
    else:
        print("No models module auto-detected. You can pass --models your.module.path")
        print("Attempting common names anyway...")

    # Try to import the models module and get Base
    # Base = None
    # tried = []
    # if models_mod:
    #     try:
    #         m = importlib.import_module(models_mod)
    #         Base = getattr(m, "Base", None)
    #         if Base is None:
    #             # maybe exported as declarative_base() named 'Base' else search
    #             for name in ("Base", "base", "metadata"):
    #                 if hasattr(m, name):
    #                     Base = getattr(m, name)
    #                     break
    #         print("Imported", models_mod, " Base:", bool(Base))
    #     except Exception as e:
    #         print("Error importing models module:", repr(e))
    # else:
    #     # try all the common names
    #     for mod in COMMON_MODEL_MODULES:
    #         try:
    #             m = importlib.import_module(mod)
    #             Base = getattr(m, "Base", None)
    #             if Base:
    #                 print("Imported", mod, "-> Base found.")
    #                 models_mod = mod
    #                 break
    #         except Exception:
    #             tried.append(mod)
    #             continue

    # if Base is None:
    #     print("\nCould not auto-detect Base. Open your models file and ensure you export `Base = declarative_base()`.")
    #     print("If your models are in e.g. myapp.models, run:\n  python debug_create_tables.py --models myapp.models")
    #     sys.exit(1)

    # If DB URL found, try to create tables there, otherwise create sqlite file next to project
    if db_url:
        # Normalize sqlite file path detection
        try:
            url_obj = make_url(db_url)
            if url_obj.drivername.startswith("sqlite"):
                # For sqlite, extract file path
                # For async, url might be like sqlite+aiosqlite:///C:/path/db.sqlite3
                # make_url keeps "database" attribute as path
                db_path = Path(url_obj.database) if url_obj.database else None
                if db_path:
                    print("\nSQLite DB file path detected:", db_path)
                    exists = db_path.exists()
                    print("File exists:", exists)
                    if exists:
                        tables = list_sqlite_tables_file(db_path)
                        print("Existing sqlite tables:", tables)
                # choose async vs sync create based on drivername
                if "aiosqlite" in url_obj.drivername or "+async" in db_url or "async" in db_url:
                    print("\nUsing async create path.")
                    asyncio.run(create_tables_async(db_url, Base))
                else:
                    create_tables_sync(db_url, Base)
            else:
                # non-sqlite DB (postgres/mysql) - use sync create
                print("\nNon-sqlite DB detected:", url_obj.drivername)
                create_tables_sync(db_url, Base)
        except Exception as e:
            print("Error handling DB URL:", repr(e))
            print("Attempting sync create with raw DB URL...")
            create_tables_sync(db_url, Base)
    else:
        # no db_url; create a local sqlite file 'debug_db.sqlite3'
        local = Path.cwd() / "debug_db.sqlite3"
        print("\nNo DB URL found. Creating local debug sqlite file at:", local)
        local_url = f"sqlite:///{local}"
        create_tables_sync(local_url, Base)
        if local.exists():
            print("Local debug DB created. Tables:")
            print(list_sqlite_tables_file(local))

if __name__ == "__main__":
    main()
