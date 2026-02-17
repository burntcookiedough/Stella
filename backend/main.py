
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import os

# Import our modules
from analytics.ingest import load_data
from analytics.features import compute_features, get_latest_user_stats
from analytics.anomaly import detect_anomalies, generate_llm_summary
from llm.engine import analyze_health_data

# Initialize App
app = FastAPI(title="Stella API", version="1.0")

# Allow CORS (for Streamlit frontend running on different port)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global Data Cache (naive approach for demo)
# In production, this would be a database connection
DATA_CACHE = None

@app.on_event("startup")
async def startup_event():
    print("🚀 Application Startup: Loading Data...")
    try:
        get_data()
        print("✅ Startup Complete: Data Loaded")
    except Exception as e:
        print(f"❌ Startup Failed: Data Load Error: {e}")

def get_data():
    """Lazy loads data once on startup or first request"""
    global DATA_CACHE
    if DATA_CACHE is None:
        print("📥 Loading Data Cache...")
        try:
            # Point to local data/raw directory relative to root execution context
            # Assuming backend is run from project root (python -m backend.main)
            data_dir = os.path.join(os.getcwd(), "data", "raw")
            print(f"📂 Reading from: {data_dir}")
            
            print("   - Loading CSVs...")
            df = load_data(data_dir)
            print(f"   - CSV Loaded. Rows: {len(df)}")
            
            print("   - Computing Features...")
            df = compute_features(df)
            
            print("   - Detecting Anomalies...")
            df = detect_anomalies(df)
            
            DATA_CACHE = df
            print("✅ Data Cache Ready.")
        except Exception as e:
            print(f"❌ Data Loading Failed: {e}")
            raise e
    return DATA_CACHE

@app.get("/")
def read_root():
    return {"status": "ok", "service": "Stella Health Analytics"}

@app.get("/users")
def get_users():
    """List all available user IDs for testing"""
    df = get_data()
    users = df['id'].unique().tolist()
    return {"count": len(users), "users": [int(u) for u in users]}

class AnalysisResponse(BaseModel):
    user_id: int
    date: str
    metrics: dict
    anomalies: dict
    ai_analysis: str

@app.post("/analyze/{user_id}", response_model=AnalysisResponse)
def analyze_user(user_id: int):
    """
    Triggers full analysis pipeline for a specific user:
    1. Retrieve latest stats
    2. Check for anomalies
    3. Generate LLM insight
    """
    df = get_data()
    
    # Check if user exists
    if user_id not in df['id'].unique():
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get structured stats
    stats = get_latest_user_stats(df, user_id)
    if not stats:
        raise HTTPException(status_code=404, detail="No data available for user")

    # Generate LLM Prompt JSON
    llm_input = generate_llm_summary(stats)

    # Call LLM
    print(f"🤖 Generating AI Insight for User {user_id}...")
    ai_text = analyze_health_data(llm_input)
    
    return {
        "user_id": user_id,
        "date": stats.get("date"),
        "metrics": {
            "steps": stats.get("steps"),
            "sleep_minutes": stats.get("sleep_minutes"),
            "health_score": stats.get("health_score"),
            "steps_trend": stats.get("steps_trend")
        },
        "anomalies": stats.get("anomalies"),
        "ai_analysis": ai_text
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="127.0.0.1", port=8000, reload=True)
