import requests
import json

url = "http://127.0.0.1:8000/api/register/"
data = {
    "username": "testuser_debug",
    "password": "password123",
    "full_name": "Debug User"
}

try:
    response = requests.post(url, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
