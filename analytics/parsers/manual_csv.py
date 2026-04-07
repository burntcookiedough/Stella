from __future__ import annotations

from pathlib import Path
import pandas as pd

from analytics.types import NormalizedRecord

COLUMN_ALIASES = {
    "timestamp": "timestamp",
    "date": "timestamp",
    "metric": "metric",
    "value": "value",
    "unit": "unit",
    "source": "source",
    "source_user_id": "source_user_id",
    "user_id": "source_user_id",
}


def parse_manual_csv(path: str | Path) -> list[NormalizedRecord]:
    dataframe = pd.read_csv(path)
    normalized_columns = {column: COLUMN_ALIASES.get(column.strip().lower(), column.strip().lower()) for column in dataframe.columns}
    dataframe = dataframe.rename(columns=normalized_columns)

    required = {"timestamp", "metric", "value"}
    missing = required - set(dataframe.columns)
    if missing:
        missing_csv = ", ".join(sorted(missing))
        raise ValueError(f"Manual CSV missing required columns: {missing_csv}")

    dataframe["timestamp"] = pd.to_datetime(dataframe["timestamp"])
    dataframe["unit"] = dataframe.get("unit", "unit").fillna("unit")
    dataframe["source"] = dataframe.get("source", "manual").fillna("manual")
    dataframe["source_user_id"] = dataframe.get("source_user_id", "manual-user").fillna("manual-user")

    records: list[NormalizedRecord] = []
    for row in dataframe.to_dict(orient="records"):
        records.append(
            NormalizedRecord.from_metadata(
                timestamp=row["timestamp"].to_pydatetime(),
                metric=str(row["metric"]),
                value=float(row["value"]),
                unit=str(row["unit"]),
                source=str(row["source"]),
                source_user_id=str(row["source_user_id"]),
                metadata={"input": "manual_csv"},
            )
        )
    return records
