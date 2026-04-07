from __future__ import annotations

from datetime import datetime
from pathlib import Path
import xml.etree.ElementTree as ET

from analytics.types import NormalizedRecord

TYPE_MAP = {
    "HKQuantityTypeIdentifierStepCount": ("steps", "count"),
    "HKQuantityTypeIdentifierHeartRateVariabilitySDNN": ("hrv", "ms"),
    "HKQuantityTypeIdentifierRestingHeartRate": ("resting_hr", "count/min"),
    "HKQuantityTypeIdentifierHeartRate": ("heart_rate", "count/min"),
    "HKQuantityTypeIdentifierActiveEnergyBurned": ("calories", "kcal"),
    "HKQuantityTypeIdentifierDistanceWalkingRunning": ("distance", "km"),
    "HKCategoryTypeIdentifierSleepAnalysis": ("sleep_minutes", "min"),
}


def _parse_datetime(raw_value: str) -> datetime:
    for fmt in ("%Y-%m-%d %H:%M:%S %z", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(raw_value, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unsupported Apple Health timestamp: {raw_value}")


def parse_apple_health_export(path: str | Path) -> list[NormalizedRecord]:
    records: list[NormalizedRecord] = []
    root = ET.parse(path).getroot()
    for node in root.findall("Record"):
        record_type = node.attrib.get("type")
        if record_type not in TYPE_MAP:
            continue
        metric, default_unit = TYPE_MAP[record_type]
        start = _parse_datetime(node.attrib["startDate"])
        end = _parse_datetime(node.attrib.get("endDate", node.attrib["startDate"]))
        source_name = node.attrib.get("sourceName", "apple_health")
        source_user_id = node.attrib.get("device", source_name)
        unit = node.attrib.get("unit", default_unit)

        if metric == "sleep_minutes":
            value = max((end - start).total_seconds() / 60.0, 0.0)
        else:
            try:
                value = float(node.attrib.get("value", "0"))
            except ValueError:
                continue

        records.append(
            NormalizedRecord.from_metadata(
                timestamp=start,
                metric=metric,
                value=value,
                unit=unit,
                source="apple_health",
                source_user_id=source_user_id,
                metadata={"record_type": record_type, "source_name": source_name},
            )
        )
    return records
