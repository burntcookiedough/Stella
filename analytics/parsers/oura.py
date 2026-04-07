from __future__ import annotations

from datetime import datetime
from pathlib import Path
import json

from analytics.types import NormalizedRecord

SECTION_METRICS = {
    "sleep": {
        "total_sleep_duration": ("sleep_minutes", "min", lambda value: float(value) / 60.0),
        "hr_average": ("resting_hr", "bpm", float),
        "hrv_average": ("hrv", "ms", float),
    },
    "activity": {
        "steps": ("steps", "count", float),
        "active_calories": ("calories", "kcal", float),
        "active_duration": ("active_minutes", "min", lambda value: float(value) / 60.0),
    },
}


def parse_oura_export(path: str | Path) -> list[NormalizedRecord]:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    source_user_id = str(payload.get("user_id", "oura-user"))
    records: list[NormalizedRecord] = []

    for section, metric_map in SECTION_METRICS.items():
        for row in payload.get(section, []):
            timestamp = datetime.fromisoformat(row["day"])
            for field_name, (metric, unit, transform) in metric_map.items():
                if field_name not in row:
                    continue
                records.append(
                    NormalizedRecord.from_metadata(
                        timestamp=timestamp,
                        metric=metric,
                        value=transform(row[field_name]),
                        unit=unit,
                        source="oura",
                        source_user_id=source_user_id,
                        metadata={"section": section, "field": field_name},
                    )
                )
    return records
