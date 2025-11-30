import os
import django
import sys

# Setup Django environment
sys.path.append('c:/Users/sreej/OneDrive/Desktop/whatsap/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
django.setup()

from django.db import connection
from core.models import User
from django.db.models import Q

def check_schema():
    print("--- Checking Database Schema ---")
    with connection.cursor() as cursor:
        cursor.execute("DESCRIBE core_user;")
        rows = cursor.fetchall()
        for row in rows:
            if row[0] == 'profile_picture':
                print(f"Column: {row[0]}, Type: {row[1]}")

def test_large_update():
    print("\n--- Testing Large Profile Update ---")
    try:
        user = User.objects.first()
        if not user:
            print("No user found to test.")
            return

        # Create a 1MB dummy base64 string
        large_data = "data:image/jpeg;base64," + "A" * (1024 * 1024) 
        print(f"Attempting to save {len(large_data)} bytes to profile_picture for user {user.username}...")
        
        user.profile_picture = large_data
        user.save()
        print("SUCCESS: Large profile picture saved to DB.")
        
        # Verify retrieval
        user.refresh_from_db()
        print(f"Retrieved length: {len(user.profile_picture)}")
        
    except Exception as e:
        print(f"FAILED: {e}")

def test_search():
    print("\n--- Testing Search Logic ---")
    query = "sree" # Assuming 'sreej' exists
    print(f"Searching for '{query}'...")
    
    users = User.objects.filter(
        Q(username__icontains=query) | Q(full_name__icontains=query)
    )
    print(f"Found {users.count()} users:")
    for u in users:
        print(f" - {u.username} ({u.full_name})")

if __name__ == "__main__":
    check_schema()
    test_search()
    
    print("\n--- Attempting to increase max_allowed_packet ---")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SET GLOBAL max_allowed_packet=67108864;")
            print("Command executed. Note: This might require a server restart or new connection to take effect.")
    except Exception as e:
        print(f"Could not set max_allowed_packet: {e}")

    test_large_update()
