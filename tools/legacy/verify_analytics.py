
from analytics.ingest import load_data
from analytics.features import compute_features, get_latest_user_stats
from analytics.anomaly import detect_anomalies, generate_llm_summary

def main():
    print("🚀 Starting Analytics Verification...")

    # 1. Test Ingestion
    try:
        print("📥 Loading Data...")
        df = load_data("data/raw")
    except Exception as e:
        print(f"❌ Failed to load data: {e}")
        return

    # 2. Test Feature Engineering
    print("⚙️ Computing Features...")
    df = compute_features(df)
    
    # Check if new columns exist
    required_cols = ['avg_steps_7d', 'sleep_zscore', 'health_score']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"❌ Missing features: {missing}")
        return
    else:
        print("✅ Features computed successfully.")

    # 3. Test Anomaly Detection
    print("🕵️ Detecting Anomalies...")
    df = detect_anomalies(df)
    
    anomalies = df[df['is_sleep_anomaly'] | df['is_steps_anomaly']]
    print(f"✅ Found {len(anomalies)} anomalous days out of {len(df)} total records.")

    # 4. Test User Summary Generation (Simulate API request)
    sample_user = df['id'].iloc[0]
    print(f"👤 Generating summary for user {sample_user}...")
    
    latest_stats = get_latest_user_stats(df, sample_user)
    print("📊 Latest Stats:", latest_stats)
    
    llm_input = generate_llm_summary(latest_stats)
    print("🤖 LLM Input JSON:", llm_input)

    print("\n✅ Verification Complete! Analytics module is ready.")

if __name__ == "__main__":
    main()
