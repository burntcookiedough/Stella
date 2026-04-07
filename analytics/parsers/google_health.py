from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
import json

from analytics.types import NormalizedRecord

DATA_SOURCE_MAP = {
    "com.google.step_count.delta": ("steps", "count"),
    "com.google.calories.expended": ("calories", "kcal"),
    "com.google.heart_rate.bpm": ("heart_rate", "bpm"),
    "com.google.resting_heart_rate.bpm": ("resting_hr", "bpm"),
    "com.google.heart_minutes": ("active_minutes", "min"),
    "com.google.hrv": ("hrv", "ms"),
}


def _parse_nanos(raw_value: str | int | None) -> datetime:
    if raw_value is None:
        return datetime.now(UTC)
    return datetime.fromtimestamp(int(raw_value) / 1_000_000_000, tz=UTC)


def parse_google_health_export(path: str | Path) -> list[NormalizedRecord]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    dataset = payload if isinstance(payload, list) else payload.get("points", [])
    records: list[NormalizedRecord] = []

    for item in dataset:
        data_type = item.get("dataTypeName") or item.get("metric")
        if data_type not in DATA_SOURCE_MAP:
            continue
        metric, default_unit = DATA_SOURCE_MAP[data_type]
        values = item.get("fitValue", [])
        if values:
            value_node = values[0]
            value = (
                value_node.get("fpVal")
                or value_node.get("intVal")
                or value_node.get("mapVal", [{}])[0].get("value", {}).get("fpVal")
                or 0
            )
        else:
            value = item.get("value", 0)
        records.append(
            NormalizedRecord.from_metadata(
                timestamp=_parse_nanos(item.get("startTimeNanos")),
                metric=metric,
                value=float(value),
                unit=item.get("unit", default_unit),
                source="google_health",
                source_user_id=str(item.get("originDataSourceId", "google-user")),
                metadata={"data_type_name": data_type},
            )
        )
    return records
