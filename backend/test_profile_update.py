import requests
import json
import base64

BASE_URL = "https://a-whatsap-replica.onrender.com/api"

def test_large_profile_update():
    # 1. Login
    login_url = f"{BASE_URL}/auth/login"
    login_payload = {
        "username": "testuser_script",
        "password": "testpassword"
    }
    
    print(f"Logging in...")
    try:
        resp = requests.post(login_url, json=login_payload)
        if resp.status_code != 200:
            print(f"Login failed: {resp.status_code} {resp.text}")
            return
        token = resp.json()["access_token"]
        print("Login successful.")
    except Exception as e:
        print(f"Login error: {e}")
        return

    # 2. Update with LARGE payload (simulate 50KB image)
    profile_url = f"{BASE_URL}/auth/profile"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # Create a dummy base64 string (~50KB)
    large_data = "a" * 50000
    large_image = f"data:image/png;base64,{large_data}"
    
    update_payload = {
        "full_name": "Large Payload User",
        "about": "Testing large payload...",
        "profile_picture": large_image
    }
    
    print(f"Sending update with {len(large_image)} chars...")
    try:
        resp = requests.patch(profile_url, json=update_payload, headers=headers)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code != 200:
            print(f"Response: {resp.text}")
        else:
            print("Update successful!")
    except Exception as e:
        print(f"Update error: {e}")

if __name__ == "__main__":
    test_large_profile_update()
