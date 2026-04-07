from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
import json


@dataclass(slots=True)
class NormalizedRecord:
    timestamp: datetime
    metric: str
    value: float
    unit: str
    source: str
    source_user_id: str
    metadata_json: str = "{}"

    @classmethod
    def from_metadata(
        cls,
        *,
        timestamp: datetime,
        metric: str,
        value: float,
        unit: str,
        source: str,
        source_user_id: str,
        metadata: dict | None = None,
    ) -> "NormalizedRecord":
        return cls(
            timestamp=timestamp,
            metric=metric,
            value=float(value),
            unit=unit,
            source=source,
            source_user_id=str(source_user_id),
            metadata_json=json.dumps(metadata or {}, sort_keys=True),
        )

    def to_row(self) -> dict:
        row = asdict(self)
        row["timestamp"] = self.timestamp.isoformat(sep=" ")
        return row
