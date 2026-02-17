
import subprocess
import time
import requests
import sys
import threading

def run_server():
    """Starts Uvicorn server"""
    subprocess.run([sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"], 
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

def main():
    print("🚀 Starting Backend Verification...")
    
    # Start server in robust thread/process
    server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", "8000"],
        text=True
    )
    
    print("⏳ Waiting for server to start (5s)...")
    time.sleep(5) 

    base_url = "http://127.0.0.1:8000"
    
    try:
        # 1. Test Health Check
        print("\n🔹 Testing Root Endpoint (GET /)...")
        resp = requests.get(f"{base_url}/")
        print(f"Status: {resp.status_code}")
        print(f"Response: {resp.json()}")
        if resp.status_code != 200:
            raise Exception("Root endpoint failed")

        # 2. Get Users
        print("\n🔹 Fetching Available Users (GET /users)...")
        resp = requests.get(f"{base_url}/users")
        users = resp.json().get("users", [])
        print(f"Found {len(users)} users. Sample: {users[:3]}")
        
        if not users:
            raise Exception("No users found")
            
        test_user_id = users[0]

        # 3. Test Full Analysis
        print(f"\n🔹 Testing Analysis Pipeline for User {test_user_id} (POST /analyze)...")
        print("Note: This calls Ollama, so it might take 5-10 seconds.")
        
        start_time = time.time()
        resp = requests.post(f"{base_url}/analyze/{test_user_id}")
        elapsed = time.time() - start_time
        
        print(f"⏱️ Time taken: {elapsed:.2f}s")
        print(f"Status: {resp.status_code}")
        
        if resp.status_code == 200:
            data = resp.json()
            print("\n✅ API Response Success!")
            print(f"User: {data['user_id']}")
            print(f"Health Score: {data['metrics']['health_score']}")
            print(f"AI Insight Preview: {data['ai_analysis'][:100]}...")
        else:
            print(f"❌ Analysis Failed: {resp.text}")

    except Exception as e:
        print(f"\n❌ Verification Error: {e}")
        # Print server logs if failed
        outs, errs = server_process.communicate(timeout=1)
        print("Server Stdout:", outs)
        print("Server Stderr:", errs)

    finally:
        print("\n🛑 Stopping Server...")
        server_process.terminate()
        server_process.wait()

if __name__ == "__main__":
    main()
