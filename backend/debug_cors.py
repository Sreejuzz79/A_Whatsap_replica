import requests

TARGET_URL = "https://a-whatsap-replica.onrender.com/api/contacts/"
ORIGIN = "https://whatsap-replica-7ln1.vercel.app"

def check_cors():
    print(f"Testing CORS for Origin: {ORIGIN}")
    headers = {
        "Origin": ORIGIN,
        "Access-Control-Request-Method": "GET",
        "Access-Control-Request-Headers": "authorization"
    }
    
    try:
        response = requests.options(TARGET_URL, headers=headers)
        print(f"Status Code: {response.status_code}")
        print("Headers:")
        for k, v in response.headers.items():
            if "access-control" in k.lower():
                print(f"  {k}: {v}")
        
        if response.headers.get("access-control-allow-origin") == ORIGIN:
            print("\nSUCCESS: CORS is correctly configured for this Origin.")
        else:
            print("\nFAILURE: Access-Control-Allow-Origin header is missing or wrong.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_cors()
