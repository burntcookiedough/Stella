from __future__ import annotations

import math

import pandas as pd


def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    v2 stores materialized features in DuckDB already.
    """
    return df.copy()


def get_latest_user_stats(df: pd.DataFrame, user_id: int | str) -> dict:
    frame = df[df["source_user_id"].astype(str) == str(user_id)].sort_values("day")
    if frame.empty:
        return {}

    latest = frame.iloc[-1]
    previous_window = frame.tail(7)
    latest_steps = _to_number(latest.get("steps"))
    mean_steps = previous_window["steps"].dropna().mean() if "steps" in previous_window else float("nan")
    steps_trend = "stable"
    if not math.isnan(mean_steps):
        if latest_steps > mean_steps * 1.1:
            steps_trend = "increasing"
        elif latest_steps < mean_steps * 0.9:
            steps_trend = "decreasing"

    return {
        "date": str(latest["day"]),
        "steps": int(latest_steps or 0),
        "steps_7d_avg": int(mean_steps) if not math.isnan(mean_steps) else 0,
        "steps_trend": steps_trend,
        "sleep_minutes": int(_to_number(latest.get("sleep_minutes")) or 0),
        "sleep_7d_avg": int(previous_window["sleep_minutes"].dropna().mean()) if "sleep_minutes" in previous_window else 0,
        "health_score": round(_to_number(latest.get("health_score")) or 0, 1),
        "anomalies": {
            "low_sleep": bool(latest.get("anomaly_low_sleep")),
            "low_activity": bool(latest.get("anomaly_low_activity")),
            "high_resting_hr": bool(latest.get("anomaly_high_resting_hr")),
        },
    }


def _to_number(value: object) -> float:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return 0.0
    return float(value)
