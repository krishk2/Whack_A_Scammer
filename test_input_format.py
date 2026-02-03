import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

def test_exact_json_input():
    url = "http://127.0.0.1:8000/detect"
    
    api_key = os.getenv("SERVICE_API_KEY")
    if not api_key:
        print("Error: SERVICE_API_KEY not found in .env")
        return

    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    # EXACT payload provided by user
    payload = { 
        "sessionId": "wertyu-dfghj-ertyui", 
        "message": { 
            "sender": "scammer", 
            "text": "Share your UPI ID to avoid account suspension.", 
            "timestamp": "2026-01-21T10:17:10Z" 
        }, 
        "conversationHistory": [ 
            { 
            "sender": "scammer", 
            "text": "Your bank account will be blocked today. Verify immediately.", 
            "timestamp": "2026-01-21T10:15:30Z" 
            }, 
            { 
            "sender": "user", 
            "text": "Why will my account be blocked?", 
            "timestamp": "2026-01-21T10:16:10Z" 
            } 
        ], 
        "metadata": { 
            "channel": "SMS", 
            "language": "English", 
            "locale": "IN" 
        } 
    }
    
    print("Sending Payload:")
    print(json.dumps(payload, indent=2))
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        
        print("\nResponse Status Code:", response.status_code)
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
        
        if response.status_code == 200:
            print("\nSUCCESS: Input format accepted and processed correctly.")
        else:
            print("\nFAILED: Server returned error.")

    except Exception as e:
        print(f"\nRequest Error: {e}")

if __name__ == "__main__":
    test_exact_json_input()
