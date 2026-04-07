from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
from typing import Any
import uuid

import duckdb
import pandas as pd

from analytics.types import NormalizedRecord

SUM_METRICS = {
    "steps",
    "sleep_minutes",
    "time_in_bed_minutes",
    "calories",
    "active_minutes",
    "very_active_minutes",
    "fairly_active_minutes",
    "lightly_active_minutes",
    "sedentary_minutes",
}

ROLLING_METRICS = ("steps", "sleep_minutes", "resting_hr", "hrv")


class HealthStore:
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self) -> duckdb.DuckDBPyConnection:
        return duckdb.connect(str(self.db_path))

    def _init_schema(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS import_runs (
                    import_id VARCHAR PRIMARY KEY,
                    source VARCHAR NOT NULL,
                    file_count INTEGER NOT NULL,
                    record_count INTEGER NOT NULL,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS raw_events (
                    import_id VARCHAR NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    metric VARCHAR NOT NULL,
                    value DOUBLE NOT NULL,
                    unit VARCHAR NOT NULL,
                    source VARCHAR NOT NULL,
                    source_user_id VARCHAR NOT NULL,
                    ingested_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    metadata_json VARCHAR NOT NULL
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS overview_daily (
                    source_user_id VARCHAR NOT NULL,
                    day DATE NOT NULL,
                    steps DOUBLE,
                    sleep_minutes DOUBLE,
                    calories DOUBLE,
                    active_minutes DOUBLE,
                    resting_hr DOUBLE,
                    hrv DOUBLE,
                    health_score DOUBLE,
                    steps_zscore DOUBLE,
                    sleep_zscore DOUBLE,
                    resting_hr_zscore DOUBLE,
                    hrv_zscore DOUBLE,
                    anomaly_low_sleep BOOLEAN,
                    anomaly_low_activity BOOLEAN,
                    anomaly_high_resting_hr BOOLEAN,
                    updated_at TIMESTAMP NOT NULL,
                    PRIMARY KEY (source_user_id, day)
                );
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS correlation_pairs (
                    source_user_id VARCHAR NOT NULL,
                    metric_a VARCHAR NOT NULL,
                    metric_b VARCHAR NOT NULL,
                    lag_days INTEGER NOT NULL,
                    correlation DOUBLE NOT NULL,
                    sample_size INTEGER NOT NULL,
                    updated_at TIMESTAMP NOT NULL
                );
                """
            )

    def ingest_records(self, source: str, records: Iterable[NormalizedRecord], file_count: int) -> dict[str, Any]:
        rows = [record.to_row() for record in records]
        if not rows:
            raise ValueError("No normalized records were produced for this import.")

        import_id = str(uuid.uuid4())
        frame = pd.DataFrame(rows)
        frame.insert(0, "import_id", import_id)
        with self.connect() as conn:
            conn.register("events_frame", frame)
            conn.execute(
                """
                INSERT INTO raw_events (
                    import_id,
                    timestamp,
                    metric,
                    value,
                    unit,
                    source,
                    source_user_id,
                    metadata_json
                )
                SELECT
                    import_id,
                    timestamp,
                    metric,
                    value,
                    unit,
                    source,
                    source_user_id,
                    metadata_json
                FROM events_frame
                """
            )
            conn.execute(
                "INSERT INTO import_runs (import_id, source, file_count, record_count) VALUES (?, ?, ?, ?)",
                [import_id, source, file_count, len(frame)],
            )
        return {
            "import_id": import_id,
            "source": source,
            "file_count": file_count,
            "record_count": len(frame),
            "users": sorted(frame["source_user_id"].astype(str).unique().tolist()),
        }

    def has_events(self) -> bool:
        with self.connect() as conn:
            count = conn.execute("SELECT COUNT(*) FROM raw_events").fetchone()[0]
        return bool(count)

    def list_users(self) -> list[str]:
        with self.connect() as conn:
            rows = conn.execute("SELECT DISTINCT source_user_id FROM raw_events ORDER BY source_user_id").fetchall()
        return [row[0] for row in rows]

    def get_latest_user(self) -> str | None:
        with self.connect() as conn:
            row = conn.execute(
                """
                SELECT source_user_id
                FROM raw_events
                ORDER BY timestamp DESC
                LIMIT 1
                """
            ).fetchone()
        return row[0] if row else None

    def fetch_raw_events(self, source_user_id: str | None = None) -> pd.DataFrame:
        query = "SELECT * FROM raw_events"
        params: list[Any] = []
        if source_user_id:
            query += " WHERE source_user_id = ?"
            params.append(source_user_id)
        with self.connect() as conn:
            return conn.execute(query, params).df()

    def replace_overview(self, dataframe: pd.DataFrame) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM overview_daily")
            if not dataframe.empty:
                conn.register("overview_frame", dataframe)
                conn.execute("INSERT INTO overview_daily SELECT * FROM overview_frame")

    def replace_correlations(self, dataframe: pd.DataFrame) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM correlation_pairs")
            if not dataframe.empty:
                conn.register("correlation_frame", dataframe)
                conn.execute("INSERT INTO correlation_pairs SELECT * FROM correlation_frame")

    def fetch_overview(self, source_user_id: str) -> pd.DataFrame:
        with self.connect() as conn:
            return conn.execute(
                """
                SELECT *
                FROM overview_daily
                WHERE source_user_id = ?
                ORDER BY day
                """,
                [source_user_id],
            ).df()

    def fetch_correlation_pairs(self, source_user_id: str, lag_days: int | None = None) -> pd.DataFrame:
        query = """
            SELECT *
            FROM correlation_pairs
            WHERE source_user_id = ?
        """
        params: list[Any] = [source_user_id]
        if lag_days is not None:
            query += " AND lag_days = ?"
            params.append(lag_days)
        query += " ORDER BY ABS(correlation) DESC, metric_a, metric_b"
        with self.connect() as conn:
            return conn.execute(query, params).df()
