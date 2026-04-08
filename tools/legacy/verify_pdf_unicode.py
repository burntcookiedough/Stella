
from backend.report import create_health_report
import sys

def verify_unicode_pdf():
    print("🚀 Verifying PDF Generation with Unicode...")
    
    stats = {
        'health_score': 85,
        'steps': 10000,
        'sleep_minutes': 480,
        'steps_trend': 'increasing'
    }
    
    # Test with emojis and special chars that might crash FPDF
    ai_text = "Status: Excellent! 🌟 Great job on hitting 10k steps. 🚶‍♂️ Keep it up! 💪"
    
    try:
        pdf_bytes = create_health_report(12345, stats, ai_text)
        print(f"✅ PDF Generated Successfully. Size: {len(pdf_bytes)} bytes")
        
        # Check signature
        if pdf_bytes.startswith(b"%PDF"):
             print("✅ Valid PDF Signature.")
        else:
             print("❌ Invalid Signature.")
             
    except Exception as e:
        print(f"❌ Failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    verify_unicode_pdf()
