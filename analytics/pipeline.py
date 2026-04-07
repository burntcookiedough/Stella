from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any
import math

import numpy as np
import pandas as pd

from analytics.parsers import (
    parse_apple_health_export,
    parse_fitbit_bundle,
    parse_garmin_fit,
    parse_google_health_export,
    parse_manual_csv,
    parse_oura_export,
)
from analytics.store import HealthStore, ROLLING_METRICS, SUM_METRICS


class HealthAnalyticsService:
    def __init__(self, store: HealthStore) -> None:
        self.store = store

    def bootstrap_fitbit_sample(self, data_dir: str | Path) -> dict[str, Any] | None:
        root = Path(data_dir)
        candidate_paths = [root / "dailyActivity_merged.csv", root / "sleepDay_merged.csv"]
        if self.store.has_events() or not any(path.exists() for path in candidate_paths):
            return None
        return self.ingest_paths(candidate_paths, source="fitbit")

    def ingest_paths(self, paths: list[str | Path], source: str | None = None) -> dict[str, Any]:
        resolved_paths = [Path(path) for path in paths]
        inferred_source = source or self._infer_source(resolved_paths)
        if inferred_source == "apple_health":
            records = parse_apple_health_export(resolved_paths[0])
        elif inferred_source == "google_health":
            records = parse_google_health_export(resolved_paths[0])
        elif inferred_source == "fitbit":
            records = parse_fitbit_bundle(resolved_paths)
        elif inferred_source == "oura":
            records = parse_oura_export(resolved_paths[0])
        elif inferred_source == "garmin":
            records = parse_garmin_fit(resolved_paths[0])
        elif inferred_source == "manual":
            records = parse_manual_csv(resolved_paths[0])
        else:
            raise ValueError(f"Unsupported source '{inferred_source}'.")

        result = self.store.ingest_records(inferred_source, records, len(resolved_paths))
        self.refresh_materializations()
        return result

    def _infer_source(self, paths: list[Path]) -> str:
        names = {path.name.lower() for path in paths}
        if "export.xml" in names:
            return "apple_health"
        if "dailyactivity_merged.csv" in names or "sleepday_merged.csv" in names:
            return "fitbit"
        suffix = paths[0].suffix.lower()
        stem = paths[0].stem.lower()
        if suffix == ".json" and "oura" in stem:
            return "oura"
        if suffix == ".json":
            return "google_health"
        if suffix == ".fit":
            return "garmin"
        if suffix == ".csv":
            return "manual"
        raise ValueError(f"Unable to infer import source from: {', '.join(sorted(names))}")

    def refresh_materializations(self) -> None:
        raw_events = self.store.fetch_raw_events()
        if raw_events.empty:
            self.store.replace_overview(pd.DataFrame())
            self.store.replace_correlations(pd.DataFrame())
            return

        raw_events["timestamp"] = pd.to_datetime(raw_events["timestamp"])
        raw_events["day"] = raw_events["timestamp"].dt.date
        daily_rows: list[dict[str, Any]] = []

        for (source_user_id, day, metric), group in raw_events.groupby(["source_user_id", "day", "metric"]):
            reducer = group["value"].sum() if metric in SUM_METRICS else group["value"].mean()
            daily_rows.append({"source_user_id": source_user_id, "day": day, "metric": metric, "value": float(reducer)})

        daily = pd.DataFrame(daily_rows)
        overview = (
            daily.pivot_table(index=["source_user_id", "day"], columns="metric", values="value")
            .reset_index()
            .rename_axis(columns=None)
            .sort_values(["source_user_id", "day"])
        )

        for column in ("steps", "sleep_minutes", "calories", "active_minutes", "resting_hr", "hrv"):
            if column not in overview.columns:
                overview[column] = np.nan

        overview["health_score"] = (
            np.minimum(overview["steps"].fillna(0) / 10000.0, 1.0) * 45
            + np.maximum(0, 1 - (overview["sleep_minutes"].fillna(0) - 480).abs() / 240.0) * 35
            + np.minimum(overview["active_minutes"].fillna(0) / 60.0, 1.0) * 20
        )

        for metric in ROLLING_METRICS:
            overview[f"{metric}_zscore"] = (
                overview.groupby("source_user_id")[metric]
                .transform(lambda series: _rolling_zscore(series.astype(float)))
                .fillna(0.0)
            )

        overview["anomaly_low_sleep"] = overview["sleep_minutes_zscore"] <= -1.5
        overview["anomaly_low_activity"] = overview["steps_zscore"] <= -1.5
        overview["anomaly_high_resting_hr"] = overview["resting_hr_zscore"] >= 1.5
        overview["updated_at"] = datetime.now(UTC)

        overview = overview[
            [
                "source_user_id",
                "day",
                "steps",
                "sleep_minutes",
                "calories",
                "active_minutes",
                "resting_hr",
                "hrv",
                "health_score",
                "steps_zscore",
                "sleep_minutes_zscore",
                "resting_hr_zscore",
                "hrv_zscore",
                "anomaly_low_sleep",
                "anomaly_low_activity",
                "anomaly_high_resting_hr",
                "updated_at",
            ]
        ].rename(columns={"sleep_minutes_zscore": "sleep_zscore"})

        correlations = self._build_correlation_pairs(overview)
        self.store.replace_overview(overview)
        self.store.replace_correlations(correlations)

    def _build_correlation_pairs(self, overview: pd.DataFrame) -> pd.DataFrame:
        metric_columns = ["steps", "sleep_minutes", "calories", "active_minutes", "resting_hr", "hrv", "health_score"]
        rows: list[dict[str, Any]] = []

        for source_user_id, group in overview.groupby("source_user_id"):
            numeric = group[metric_columns].copy()
            for lag_days in (0, 1):
                shifted = numeric.shift(-lag_days) if lag_days else numeric
                for index, metric_a in enumerate(metric_columns):
                    for metric_b in metric_columns[index + 1 :]:
                        pair_frame = pd.DataFrame({"a": numeric[metric_a], "b": shifted[metric_b]}).dropna()
                        if len(pair_frame) < 3:
                            continue
                        correlation = pair_frame["a"].corr(pair_frame["b"])
                        if correlation is None or math.isnan(float(correlation)):
                            continue
                        rows.append(
                            {
                                "source_user_id": source_user_id,
                                "metric_a": metric_a,
                                "metric_b": metric_b,
                                "lag_days": lag_days,
                                "correlation": float(correlation),
                                "sample_size": int(len(pair_frame)),
                                "updated_at": datetime.now(UTC),
                            }
                        )

        return pd.DataFrame(rows)

    def get_overview(self, source_user_id: str | None = None) -> dict[str, Any]:
        user_id = source_user_id or self.store.get_latest_user()
        if user_id is None:
            return {"available_users": [], "selected_user": None, "latest": None, "trend_slices": [], "anomalies": []}

        overview = self.store.fetch_overview(user_id)
        if overview.empty:
            return {
                "available_users": self.store.list_users(),
                "selected_user": user_id,
                "latest": None,
                "trend_slices": [],
                "anomalies": [],
            }

        latest = overview.iloc[-1]
        trend_columns = ["steps", "sleep_minutes", "resting_hr", "hrv", "health_score"]
        trend_slices = [
            {"day": str(row["day"]), **{column: _safe_float(row.get(column)) for column in trend_columns}}
            for row in overview.tail(21).to_dict(orient="records")
        ]
        anomaly_rows = []
        for row in overview.tail(14).to_dict(orient="records"):
            if row["anomaly_low_sleep"] or row["anomaly_low_activity"] or row["anomaly_high_resting_hr"]:
                anomaly_rows.append(
                    {
                        "day": str(row["day"]),
                        "low_sleep": bool(row["anomaly_low_sleep"]),
                        "low_activity": bool(row["anomaly_low_activity"]),
                        "high_resting_hr": bool(row["anomaly_high_resting_hr"]),
                    }
                )

        return {
            "available_users": self.store.list_users(),
            "selected_user": user_id,
            "latest": {
                "day": str(latest["day"]),
                "steps": _safe_float(latest["steps"]),
                "sleep_minutes": _safe_float(latest["sleep_minutes"]),
                "resting_hr": _safe_float(latest["resting_hr"]),
                "hrv": _safe_float(latest["hrv"]),
                "health_score": round(_safe_float(latest["health_score"]), 1),
            },
            "trend_slices": trend_slices,
            "anomalies": anomaly_rows,
        }

    def get_correlations(self, source_user_id: str | None = None, lag_days: int | None = None) -> dict[str, Any]:
        user_id = source_user_id or self.store.get_latest_user()
        if user_id is None:
            return {"selected_user": None, "matrix": {}, "pairs": []}
        pairs = self.store.fetch_correlation_pairs(user_id, lag_days=lag_days)
        matrix: dict[str, dict[str, float]] = {}
        for row in pairs[pairs["lag_days"] == 0].to_dict(orient="records"):
            matrix.setdefault(row["metric_a"], {})[row["metric_b"]] = round(float(row["correlation"]), 3)
            matrix.setdefault(row["metric_b"], {})[row["metric_a"]] = round(float(row["correlation"]), 3)

        pair_rows = [
            {
                "metric_a": row["metric_a"],
                "metric_b": row["metric_b"],
                "lag_days": int(row["lag_days"]),
                "correlation": round(float(row["correlation"]), 3),
                "sample_size": int(row["sample_size"]),
            }
            for row in pairs.to_dict(orient="records")
        ]
        return {"selected_user": user_id, "matrix": matrix, "pairs": pair_rows}


def _rolling_zscore(series: pd.Series, window: int = 30) -> pd.Series:
    rolling_mean = series.rolling(window=window, min_periods=3).mean()
    rolling_std = series.rolling(window=window, min_periods=3).std().replace(0, np.nan)
    return (series - rolling_mean) / rolling_std


def _safe_float(value: Any) -> float | None:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return float(value)
