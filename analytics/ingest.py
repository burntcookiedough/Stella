from __future__ import annotations

from pathlib import Path

import pandas as pd

from analytics.pipeline import HealthAnalyticsService
from analytics.store import HealthStore


def load_data(data_dir: str = "data/raw") -> pd.DataFrame:
    """
    Compatibility wrapper for the v1 scripts.
    Loads Fitbit CSVs into the v2 pipeline and returns the latest user's overview frame.
    """
    store = HealthStore(Path("data/stella.duckdb"))
    service = HealthAnalyticsService(store)
    service.ingest_paths(
        [
            Path(data_dir) / "dailyActivity_merged.csv",
            Path(data_dir) / "sleepDay_merged.csv",
        ],
        source="fitbit",
    )
    user_id = store.get_latest_user()
    if user_id is None:
        return pd.DataFrame()
    return store.fetch_overview(user_id)
