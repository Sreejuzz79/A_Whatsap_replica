import requests
import json
import base64
import time

BASE_URL = "https://a-whatsap-replica.onrender.com/api"

def test_get_profile():
    # 0. Register
    register_url = f"{BASE_URL}/auth/register"
    username = f"testuser_{int(time.time())}"
    register_payload = {
        "username": username,
        "password": "testpassword",
        "full_name": "Test Script User"
    }
    
    try:
        resp = requests.post(register_url, json=register_payload)
    except Exception as e:
        return

    # 1. Login
    login_url = f"{BASE_URL}/auth/login"
    login_payload = {
        "username": username,
        "password": "testpassword"
    }
    
    try:
        resp = requests.post(login_url, json=login_payload)
        token = resp.json()["access_token"]
    except Exception as e:
        return

    # 2. GET Profile
    profile_url = f"{BASE_URL}/auth/profile"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    print(f"Testing GET /profile...")
    try:
        resp = requests.get(profile_url, headers=headers)
        print(f"GET Status Code: {resp.status_code}")
        print(f"GET Response: {resp.text}")
    except Exception as e:
        print(f"GET error: {e}")

if __name__ == "__main__":
    test_get_profile()
