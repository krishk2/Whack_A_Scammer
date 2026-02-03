import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def test_isolation():
    url = "http://127.0.0.1:8000/detect"
    api_key = os.getenv("SERVICE_API_KEY")
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    # Session A
    session_a = "SESSION_A_" + str(int(time.time()))
    print(f"--- Starting Session A: {session_a} ---")
    payload_a = {
        "sessionId": session_a,
        "message": { "sender": "scammer", "text": "Call 1111111111 to pay bill.", "timestamp": "2023-10-27T10:00:00" },
        "conversationHistory": [],
        "metadata": {"channel": "sms"}
    }
    requests.post(url, json=payload_a, headers=headers)
    print("Session A: Injected Phone '1111111111'")

    # Session B
    session_b = "SESSION_B_" + str(int(time.time()))
    print(f"\n--- Starting Session B: {session_b} ---")
    payload_b = {
        "sessionId": session_b,
        "message": { "sender": "scammer", "text": "Call 2222222222 to pay bill.", "timestamp": "2023-10-27T10:00:00" },
        "conversationHistory": [],
        "metadata": {"channel": "sms"}
    }
    requests.post(url, json=payload_b, headers=headers)
    print("Session B: Injected Phone '2222222222'")
    
    # Verify Independence
    # We can't query the DB directly via API easily without hacking the /detect response to show ALL artifacts, 
    # OR we can just rely on the 'final result' callback logic or check debug logs.
    # Actually, let's just use the fact that we can check the LOGS or trust the code structure.
    # BUT, to be sure, let's modify the test to trigger a "final callback" on Session A and see what it sends.
    
    # Trigger End on Session A
    print("\n--- Extending Session A to Trigger Callback ---")
    payload_a_final = {
        "sessionId": session_a,
        "message": { "sender": "scammer", "text": "I am blocking you now. Bye.", "timestamp": "2023-10-27T10:10:00" },
        "conversationHistory": [],
        "metadata": {"channel": "sms"}
    }
    requests.post(url, json=payload_a_final, headers=headers)
    
    print("\nCHECK SERVER LOGS:")
    print(f"1. Callback for {session_a} should ONLY have '1111111111'")
    print(f"2. It shoud NOT have '2222222222'")

if __name__ == "__main__":
    test_isolation()
