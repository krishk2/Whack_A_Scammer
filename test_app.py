from fastapi.testclient import TestClient
from main import app, memory_store
from unittest.mock import MagicMock, AsyncMock
import sys

# Patch the redis client on the existing memory_store instance
memory_store.redis = MagicMock()
import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_detect_scam():
    url = "http://127.0.0.1:8000/detect"
    
    api_key = os.getenv("SERVICE_API_KEY")
    if not api_key:
        print("Error: SERVICE_API_KEY not found in .env")
        return

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    payload = {
        "sessionId": "test-session-123",
        "message": {
            "sender": "scammer",
            "text": "Your bank account 1234567890 differs from your Aadhaar. Update immediately at http://bit.ly/scam-link or your account will be blocked.",
            "timestamp": "2023-10-27T10:00:00"
        },
        "conversationHistory": [],
        "metadata": {"channel": "sms"}
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print(f"Response Status Code: {response.status_code}")
        data = response.json()
        print(f"Response Body: {json.dumps(data, indent=2)}")
        
        assert response.status_code == 200
        
        # Assertions for AgentAPIResponse
        assert "status" in data
        assert data["status"] == "success"
        assert "reply" in data
        
        if data.get("reply"):
            print(f"Persona Agent Reply: {data['reply']}")

    except Exception as e:
        print(f"Request Error: {e}")
        raise e

if __name__ == "__main__":
    try:
        test_detect_scam()
        print("Test Passed!")
    except Exception as e:
        print(f"Test Failed: {e}")
