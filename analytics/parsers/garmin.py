from __future__ import annotations

from datetime import datetime
from pathlib import Path

from analytics.types import NormalizedRecord

try:
    from fitparse import FitFile
except ImportError:  # pragma: no cover
    FitFile = None


MESSAGE_METRICS = {
    "steps": ("steps", "count"),
    "calories": ("calories", "kcal"),
    "heart_rate": ("heart_rate", "bpm"),
    "resting_heart_rate": ("resting_hr", "bpm"),
}


def parse_garmin_fit(path: str | Path) -> list[NormalizedRecord]:
    if FitFile is None:
        raise RuntimeError("Garmin FIT import requires the optional fitparse dependency.")

    fitfile = FitFile(str(path))
    records: list[NormalizedRecord] = []
    for message in fitfile.get_messages():
        values = {field.name: field.value for field in message}
        timestamp = values.get("timestamp")
        if not isinstance(timestamp, datetime):
            continue
        source_user_id = str(values.get("user_profile_index", "garmin-user"))
        for field_name, (metric, unit) in MESSAGE_METRICS.items():
            if field_name not in values or values[field_name] is None:
                continue
            records.append(
                NormalizedRecord.from_metadata(
                    timestamp=timestamp,
                    metric=metric,
                    value=float(values[field_name]),
                    unit=unit,
                    source="garmin",
                    source_user_id=source_user_id,
                    metadata={"message_name": message.name, "field": field_name},
                )
            )
    return records
