from __future__ import annotations

import pandas as pd


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    return df.copy()


def generate_llm_summary(user_data: dict) -> dict:
    return {
        "date": user_data.get("date"),
        "metrics": {
            "steps": user_data.get("steps"),
            "sleep_minutes": user_data.get("sleep_minutes"),
            "health_score": user_data.get("health_score"),
            "resting_hr": user_data.get("resting_hr"),
            "hrv": user_data.get("hrv"),
        },
        "trends": {
            "steps_trend": user_data.get("steps_trend"),
            "avg_sleep_7d": user_data.get("sleep_7d_avg"),
        },
        "anomalies": user_data.get("anomalies", {}),
    }
