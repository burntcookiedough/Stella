import sys
import pandas as pd
from analytics.ingest import load_data
from analytics.features import compute_features
from analytics.anomaly import detect_anomalies

def main():
    try:
        df = load_data("data/raw")
        df = compute_features(df)
        df = detect_anomalies(df)
        
        num_days = df['date'].nunique()
        min_date = df['date'].min()
        max_date = df['date'].max()
        
        num_sleep_anomalies = df['is_sleep_anomaly'].sum()
        num_steps_anomalies = df['is_steps_anomaly'].sum()
        num_high_activity_anomalies = df['is_high_activity_anomaly'].sum()
        total_anomalies = num_sleep_anomalies + num_steps_anomalies + num_high_activity_anomalies
        
        columns = df.columns.tolist()
        
        with open("stats_output.txt", "w", encoding="utf-8") as f:
            f.write(f"Number of unique days: {num_days} (approx {num_days/7:.1f} weeks)\n")
            f.write(f"Date range: {min_date} to {max_date}\n")
            f.write(f"Total anomalies: {total_anomalies}\n")
            f.write(f"  - Sleep anomalies: {num_sleep_anomalies}\n")
            f.write(f"  - Steps anomalies: {num_steps_anomalies}\n")
            f.write(f"  - High activity anomalies: {num_high_activity_anomalies}\n")
            f.write(f"Columns in final dataset: {len(columns)}\n")
            f.write(f"Columns: {columns}\n")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
