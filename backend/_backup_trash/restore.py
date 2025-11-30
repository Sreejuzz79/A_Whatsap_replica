import os
import shutil

# Files and directories to restore
FILES_TO_RESTORE = [
    "manage.py",
    "whatsapp_backend",
    "check_old_db.py",
    "add_columns.py",
    "create_table_pymysql.py",
    "check_tables.py",
    "create_call_logs_table.py",
    "debug_create_tables.py",
    "debug_db.sqlite3",
    "debug_login.py",
    "debug_system.py",
    "debug_users.py",
    "fix_avatar_column.py",
    "init_mysql.py",
    "migrate_users.py",
    "test_argon2.py",
    "test_connect.py",
    "test_passlib.py",
    "test_pbkdf2.py",
    "test_register.py",
    "test_register_script.py"
]

def restore():
    current_dir = os.getcwd()
    parent_dir = os.path.dirname(current_dir)
    
    print(f"Restoring files from {current_dir} to {parent_dir}...")
    
    for item in FILES_TO_RESTORE:
        src = os.path.join(current_dir, item)
        dst = os.path.join(parent_dir, item)
        
        if os.path.exists(src):
            try:
                shutil.move(src, dst)
                print(f"Restored: {item}")
            except Exception as e:
                print(f"Error restoring {item}: {e}")
        else:
            print(f"Skipped (not found): {item}")
            
    print("Restore complete.")

if __name__ == "__main__":
    restore()
