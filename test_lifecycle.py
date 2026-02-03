import requests
import json
import os
import time
from dotenv import load_dotenv

load_dotenv()

def simulate_conversation():
    url = "http://127.0.0.1:8000/detect"
    api_key = os.getenv("SERVICE_API_KEY")
    
    headers = {
        "Content-Type": "application/json",
        "x-api-key": api_key
    }
    
    session_id = "lifecycle_test_" + str(int(time.time()))
    print(f"--- Starting Multi-Turn Simulation (Session: {session_id}) ---")

    # Turn 1: Initial Scam Attempt
    print("\n[Turn 1] Scammer: 'Hello, your electric bill is unpaid. Power will be cut.'")
    payload1 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer", "text": "Hello, your electric bill is unpaid. Power will be cut tonight unless you pay immediately.", "timestamp": "2023-10-27T10:00:00"
        },
        "conversationHistory": [],
        "metadata": {"channel": "sms"}
    }
    resp1 = requests.post(url, json=payload1, headers=headers).json()
    print(f"Persona Reply: {resp1.get('reply')}")

    # Turn 2: Providing Artifacts (Phone Number)
    print("\n[Turn 2] Scammer: 'Call this number 9988776655 to pay now.'")
    payload2 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer", "text": "Call this support number 9988776655 to pay now or we disconnect.", "timestamp": "2023-10-27T10:05:00"
        },
        # In a real front-end, you'd append the history. 
        "conversationHistory": [], 
        "metadata": {"channel": "sms"}
    }
    resp2 = requests.post(url, json=payload2, headers=headers).json()
    print(f"Persona Reply: {resp2.get('reply')}")

    # Turn 3: Providing More Artifacts (UPI & Bank)
    print("\n[Turn 3] Scammer: 'Pay to UPI electricity@upi or Account 100020003000. Do it now.'")
    payload3 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer", "text": "Pay to UPI electricity@upi or Account 100020003000. Do it now, last warning.", "timestamp": "2023-10-27T10:10:00"
        },
        "conversationHistory": [], # Ideally we'd append previous messages here
        "metadata": {"channel": "sms"}
    }
    resp3 = requests.post(url, json=payload3, headers=headers).json()
    print(f"Persona Reply: {resp3.get('reply')}")
    
    # Turn 4: Scammer Frustration
    print("\n[Turn 4] Scammer: 'Why are you asking so many questions? Do you want power cut?'")
    payload4 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer", "text": "Why are you asking so many questions? Just pay or we cut power in 5 mins.", "timestamp": "2023-10-27T10:15:00"
        },
        "conversationHistory": [],
        "metadata": {"channel": "sms"}
    }
    resp4 = requests.post(url, json=payload4, headers=headers).json()
    print(f"Persona Reply: {resp4.get('reply')}")

    # Turn 5: Scammer Ends Conversation (The Trigger)
    print("\n[Turn 5] Scammer: 'Fine, I am blocking your connection now. Bye.'")
    payload5 = {
        "sessionId": session_id,
        "message": {
            "sender": "scammer", "text": "Fine, since you are not listening, I am blocking your connection now. Don't call us back. Bye.", "timestamp": "2023-10-27T10:20:00"
        },
        "conversationHistory": [],
        "metadata": {"channel": "sms"}
    }
    resp5 = requests.post(url, json=payload5, headers=headers).json()
    print(f"Persona Reply: {resp5.get('reply')}")
    
    print("\n--- Simulation Complete ---")
    print("CHECK SERVER LOGS NOW.")
    print("You should see '[CALLBACK] Payload sent...' after Turn 5 because the scammer ended the chat.")

if __name__ == "__main__":
    simulate_conversation()
