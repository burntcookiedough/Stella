
import requests
import sys

URL = "http://127.0.0.1:8000/report/1503960366"

def verify_report():
    print("🚀 Verifying PDF Report Endpoint...")
    
    try:
        # Note: This might trigger LLM, so set timeout high
        response = requests.get(URL, timeout=120) 
        
        if response.status_code == 200:
            content_type = response.headers.get("content-type")
            print(f"✅ Status 200 OK")
            print(f"📄 Content-Type: {content_type}")
            
            if "application/pdf" in content_type:
                # Check PDF signature
                if response.content.startswith(b"%PDF"):
                    print("✅ Valid PDF Signature detected.")
                    print(f"📦 Size: {len(response.content)} bytes")
                else:
                    print("❌ Invalid File Signature (Not a PDF)")
            else:
                print(f"❌ Unexpected Content-Type: {content_type}")
        else:
            print(f"❌ Failed: {response.status_code}")
            print(response.text)

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    verify_report()
