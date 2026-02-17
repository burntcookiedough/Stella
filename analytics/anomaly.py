
import pandas as pd

def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Applies logic to flag specific rows as anomalous based on pre-calculated z-scores.
    Adds boolean columns: 'is_sleep_anomaly', 'is_steps_anomaly'.
    """
    # Thresholds
    Z_THRESHOLD_LOW = -2.0  # Significant drop
    Z_THRESHOLD_HIGH = 2.5  # Significant spike (less critical for steps unless overtraining)

    # 1. Low Sleep Anomaly
    df['is_sleep_anomaly'] = df['sleep_zscore'] < Z_THRESHOLD_LOW

    # 2. Low Activity Anomaly (Sedentary Behavior Spy)
    df['is_steps_anomaly'] = df['steps_zscore'] < Z_THRESHOLD_LOW

    # 3. High Activity Anomaly (Potential overtraining/unusual exertion)
    df['is_high_activity_anomaly'] = df['steps_zscore'] > Z_THRESHOLD_HIGH

    return df

def generate_llm_summary(user_data: dict) -> dict:
    """
    Prepares a clean, minimal JSON object for the LLM prompt.
    """
    return {
        "date": user_data.get("date"),
        "metrics": {
            "steps": user_data.get("steps"),
            "sleep_min": user_data.get("sleep_minutes"),
            "health_score": user_data.get("health_score")
        },
        "trends": {
            "steps_trend": user_data.get("steps_trend"),
            "avg_sleep_7d": user_data.get("sleep_7d_avg")
        },
        "anomalies": user_data.get("anomalies", {})
    }
