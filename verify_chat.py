
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
        
        # Enable streaming
        with requests.post(URL, json=payload, stream=True, timeout=60) as response:
            if response.status_code == 200:
                print("✅ Connection Established. Receiving stream...")
                print("🤖 Response: ", end="", flush=True)
                
                # Iterate over chunks
                for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
                    if chunk:
                        print(chunk, end="", flush=True)
                
                duration = time.time() - start_time
                print(f"\n\n⏱️ Total Time: {duration:.2f}s")
            else:
                print(f"❌ Failed: {response.status_code}")
                print(response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_chat()
