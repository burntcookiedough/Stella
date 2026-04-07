from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from analytics.parsers.apple_health import parse_apple_health_export
from analytics.parsers.fitbit import parse_fitbit_bundle
from analytics.parsers.garmin import parse_garmin_fit
from analytics.parsers.google_health import parse_google_health_export
from analytics.parsers.manual_csv import parse_manual_csv
from analytics.parsers.oura import parse_oura_export


FIXTURES = Path(__file__).parent / "fixtures" / "imports"


def test_parse_apple_health_export() -> None:
    records = parse_apple_health_export(FIXTURES / "apple_health_export.xml")
    metrics = {record.metric for record in records}
    assert {"steps", "resting_hr", "hrv", "sleep_minutes"} <= metrics


def test_parse_google_takeout_export() -> None:
    records = parse_google_health_export(FIXTURES / "google_takeout.json")
    assert len(records) == 2
    assert records[0].source == "google_health"


def test_parse_fitbit_bundle() -> None:
    records = parse_fitbit_bundle(
        [
            FIXTURES / "fitbit_dailyActivity_merged.csv",
            FIXTURES / "fitbit_sleepDay_merged.csv",
        ]
    )
    assert any(record.metric == "steps" for record in records)
    assert any(record.metric == "sleep_minutes" for record in records)


def test_parse_oura_export() -> None:
    records = parse_oura_export(FIXTURES / "oura_export.json")
    assert any(record.metric == "hrv" for record in records)
    assert any(record.metric == "calories" for record in records)


def test_parse_manual_csv() -> None:
    records = parse_manual_csv(FIXTURES / "manual_metrics.csv")
    assert len(records) == 3
    assert records[0].source == "manual"


def test_parse_manual_csv_rejects_missing_columns() -> None:
    with pytest.raises(ValueError):
        parse_manual_csv(FIXTURES / "manual_invalid.csv")


def test_parse_garmin_fit_with_mocked_dependency(monkeypatch: pytest.MonkeyPatch) -> None:
    class MockField:
        def __init__(self, name: str, value: object) -> None:
            self.name = name
            self.value = value

    class MockMessage:
        name = "record"

        def __iter__(self):
            return iter(
                [
                    MockField("timestamp", datetime(2026, 4, 4, 7, 0, 0)),
                    MockField("steps", 1234),
                    MockField("heart_rate", 63),
                ]
            )

    class MockFitFile:
        def __init__(self, _path: str) -> None:
            pass

        def get_messages(self):
            return [MockMessage()]

    monkeypatch.setattr("analytics.parsers.garmin.FitFile", MockFitFile)
    records = parse_garmin_fit(FIXTURES / "garmin_sample.fit")
    assert any(record.metric == "steps" for record in records)
