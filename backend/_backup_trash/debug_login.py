import os
import django
import sys

# Setup Django environment
sys.path.append('c:/Users/sreej/OneDrive/Desktop/whatsap/backend')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'whatsapp_backend.settings')
django.setup()

from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

def test_direct_auth():
    print("\n--- Testing Direct Django Authentication ---")
    username = 'testuser'
    password = 'password123'
    
    try:
        user = User.objects.get(username=username)
        print(f"User found: {user.username} (Active: {user.is_active})")
        
        try:
            is_valid = user.check_password(password)
            print(f"Password valid? {is_valid}")
        except Exception as e:
            print(f"Error checking password: {e}")

    except User.DoesNotExist:
        print(f"User '{username}' does not exist!")
        return

    auth_user = authenticate(username=username, password=password)
    if auth_user:
        print("SUCCESS: authenticate() returned user.")
    else:
        print("FAILURE: authenticate() returned None.")

if __name__ == "__main__":
    test_direct_auth()
