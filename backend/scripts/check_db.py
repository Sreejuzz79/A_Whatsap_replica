# scripts/check_db.py
import sqlite3, pathlib
db_file = pathlib.Path("test.db").resolve()
print("Resolved DB path:", db_file)
if not db_file.exists():
    print("DB file does NOT exist.")
else:
    conn = sqlite3.connect(str(db_file))
    cur = conn.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    print("Tables in DB:", tables)
    conn.close()
