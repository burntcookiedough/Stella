
import requests
import json
import time

URL = "http://127.0.0.1:8000/chat"
USER_ID = 1503960366  # Known user from dataset

def verify_chat():
    print("🚀 Verifying Chat Endpoint...")
    
    payload = {
        "user_id": USER_ID,
        "message": "What is my health score today?"
    }
    
    try:
        print(f"🔹 Sending Request: {payload['message']}")
        start_time = time.time()
        response = requests.post(URL, json=payload, timeout=60)
        duration = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success ({duration:.2f}s)!")
            print(f"🤖 Response: {data.get('response')}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_chat()
