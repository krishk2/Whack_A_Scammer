import requests
import json
import os
from dotenv import load_dotenv

# Load env from parent dir if needed, or current
load_dotenv()

def test_security():
    url = "http://127.0.0.1:8000/detect"
    
    # 1. Test WITHOUT Header
    print("\n[TEST 1] Request WITHOUT Header")
    try:
        response = requests.post(url, json={"dummy": "data"})
        print(f"Status: {response.status_code}")
        if response.status_code == 403:
            print("SUCCESS: Access Denied as expected.")
        else:
            print(f"FAILED: Expected 403, got {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    # 2. Test WITH WRONG Header
    print("\n[TEST 2] Request with INVALID Token")
    headers = {"x-api-key": "invalid_token_123"}
    try:
        response = requests.post(url, json={"dummy": "data"}, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Body: {response.json()}")
        if response.status_code == 403:
            print("SUCCESS: Access Denied as expected.")
        else:
            print(f"FAILED: Expected 403, got {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_security()
