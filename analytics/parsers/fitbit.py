from __future__ import annotations

from datetime import datetime
from pathlib import Path
import pandas as pd

from analytics.types import NormalizedRecord

DAILY_ACTIVITY_METRICS = {
    "TotalSteps": ("steps", "count"),
    "Calories": ("calories", "kcal"),
    "VeryActiveMinutes": ("very_active_minutes", "min"),
    "FairlyActiveMinutes": ("fairly_active_minutes", "min"),
    "LightlyActiveMinutes": ("lightly_active_minutes", "min"),
    "SedentaryMinutes": ("sedentary_minutes", "min"),
}

SLEEP_METRICS = {
    "TotalMinutesAsleep": ("sleep_minutes", "min"),
    "TotalTimeInBed": ("time_in_bed_minutes", "min"),
}


def _record_timestamp(raw_value: str) -> datetime:
    return pd.to_datetime(raw_value).to_pydatetime()


def parse_fitbit_bundle(paths: list[str | Path]) -> list[NormalizedRecord]:
    normalized_paths = [Path(path) for path in paths]
    activity_path = next((path for path in normalized_paths if "dailyactivity_merged.csv" in path.name.lower()), None)
    sleep_path = next((path for path in normalized_paths if "sleepday_merged.csv" in path.name.lower()), None)

    if activity_path is None and sleep_path is None:
        raise FileNotFoundError("Fitbit import expects dailyActivity_merged.csv or sleepDay_merged.csv.")

    records: list[NormalizedRecord] = []

    if activity_path is not None:
        activity_df = pd.read_csv(activity_path)
        for row in activity_df.to_dict(orient="records"):
            timestamp = _record_timestamp(row["ActivityDate"])
            source_user_id = str(row["Id"])
            for column, (metric, unit) in DAILY_ACTIVITY_METRICS.items():
                records.append(
                    NormalizedRecord.from_metadata(
                        timestamp=timestamp,
                        metric=metric,
                        value=row.get(column, 0) or 0,
                        unit=unit,
                        source="fitbit",
                        source_user_id=source_user_id,
                        metadata={"column": column},
                    )
                )

    if sleep_path is not None:
        sleep_df = pd.read_csv(sleep_path)
        for row in sleep_df.to_dict(orient="records"):
            timestamp = _record_timestamp(row["SleepDay"])
            source_user_id = str(row["Id"])
            for column, (metric, unit) in SLEEP_METRICS.items():
                records.append(
                    NormalizedRecord.from_metadata(
                        timestamp=timestamp,
                        metric=metric,
                        value=row.get(column, 0) or 0,
                        unit=unit,
                        source="fitbit",
                        source_user_id=source_user_id,
                        metadata={"column": column},
                    )
                )
    return records
