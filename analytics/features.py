
import pandas as pd
import numpy as np

def compute_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes rolling averages, sleep debt, and health scores.
    """
    # Ensure sorted by user and date
    df = df.sort_values(by=['id', 'date']).reset_index(drop=True)

    # 1. Rolling 7-day Averages
    df['avg_steps_7d'] = df.groupby('id')['totalsteps'].transform(lambda x: x.rolling(window=7, min_periods=1).mean())
    df['avg_sleep_7d'] = df.groupby('id')['totalminutesasleep'].transform(lambda x: x.rolling(window=7, min_periods=1).mean())

    # 2. Daily Z-Scores (Deviation from user's own mean)
    # Using expanding window for "history known so far" or full history? 
    # Let's use user's overall mean for simplicity in this demo, or rolling 30d window.
    # Rolling 30d is better for adapting to lifestyle changes.
    df['steps_zscore'] = df.groupby('id')['totalsteps'].transform(
        lambda x: (x - x.rolling(window=30, min_periods=5).mean()) / (x.rolling(window=30, min_periods=5).std() + 1e-6)
    )
    df['sleep_zscore'] = df.groupby('id')['totalminutesasleep'].transform(
        lambda x: (x - x.rolling(window=30, min_periods=5).mean()) / (x.rolling(window=30, min_periods=5).std() + 1e-6)
    )

    # 3. Sleep Variance (7-day standard deviation of sleep start time would be ideal, but we have total minutes)
    df['sleep_volatility_7d'] = df.groupby('id')['totalminutesasleep'].transform(lambda x: x.rolling(window=7).std())

    # 4. Activity Ratio (Active Minutes / Total Minutes)
    # sum of very/fairly/lightly active minutes
    df['active_minutes'] = df['veryactiveminutes'] + df['fairlyactiveminutes'] + df['lightlyactiveminutes']
    df['sedentary_ratio'] = df['sedentaryminutes'] / (df['active_minutes'] + df['sedentaryminutes'] + 1e-6)

    # 5. Composite Health Score (Simple heuristic)
    # Higher steps = good, 7-8 hours sleep (420-480 min) = good, low sedentary = good.
    # Simple score 0-100:
    # Steps component (capped at 10k)
    steps_score = np.minimum(df['totalsteps'] / 10000, 1.0) * 40 # Max 40 points
    
    # Sleep component (ideal 420-540 min)
    # Penalize deviation from 480 min (8 hours)
    sleep_diff = np.abs(df['totalminutesasleep'] - 480)
    sleep_score = np.maximum(0, (1 - (sleep_diff / 240))) * 40 # Max 40 points, drops to 0 if >4 hours off
    
    # Activity Intensity (20 pts)
    intensity_score = np.minimum(df['veryactiveminutes'] / 30, 1.0) * 20

    df['health_score'] = steps_score + sleep_score + intensity_score

    return df

def get_latest_user_stats(df: pd.DataFrame, user_id: int) -> dict:
    """
    Returns the latest row for a specific user as a dictionary, enriched with features.
    """
    user_data = df[df['id'] == user_id].sort_values(by='date')
    if user_data.empty:
        return {}
    
    latest = user_data.iloc[-1]
    prev_7d = user_data.iloc[-8:-1] if len(user_data) > 7 else user_data.iloc[:-1]

    # Calculate trends
    steps_trend = "stable"
    if latest['totalsteps'] > latest['avg_steps_7d'] * 1.1: steps_trend = "increasing"
    elif latest['totalsteps'] < latest['avg_steps_7d'] * 0.9: steps_trend = "decreasing"

    return {
        "date": str(latest['date'].date()), # Clean date string
        "steps": int(latest['totalsteps']),
        "steps_7d_avg": int(latest['avg_steps_7d']),
        "steps_trend": steps_trend,
        "sleep_minutes": int(latest['totalminutesasleep']) if not pd.isna(latest['totalminutesasleep']) else 0,
        "sleep_7d_avg": int(latest['avg_sleep_7d']) if not pd.isna(latest['avg_sleep_7d']) else 0,
        "health_score": round(latest['health_score'], 1),
        "anomalies": {
            "low_sleep": bool(latest['sleep_zscore'] < -2.0),
            "low_activity": bool(latest['steps_zscore'] < -2.0)
        }
    }
