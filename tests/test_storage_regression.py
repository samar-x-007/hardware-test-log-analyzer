from datetime import datetime, timezone
import sqlite3
from hwlog_analyzer.analysis import build_dataframe
from hwlog_analyzer.models import TestRecord as HardwareRecord
from hwlog_analyzer.regression import compare_runs
from hwlog_analyzer.storage import SQLiteRecordStore


def _record(run, status, extra=None):
    return HardwareRecord(datetime(2026, 10, 20, tzinfo=timezone.utc), run, "D1",
                          "cpu_stress", status, temperature_c=70.0,
                          extra=extra or {})


def test_sqlite_round_trip_and_duplicate_is_ignored(tmp_path):
    store = SQLiteRecordStore(tmp_path / "runs.sqlite")
    record = _record("R1", "PASS", {"lot": "L7"})
    assert store.save_records([record]) == 1
    assert store.save_records([record]) == 0
    assert store.get_records("R1") == [record]
    assert store.list_run_ids() == ["R1"]


def test_sqlite_keeps_distinct_retries_at_the_same_timestamp(tmp_path):
    store = SQLiteRecordStore(tmp_path / "runs.sqlite")
    first = _record("R1", "FAIL")
    retry = HardwareRecord(first.timestamp, first.run_id, first.device_id, first.test_name,
                           "PASS", temperature_c=first.temperature_c)
    assert store.save_records([first, retry]) == 2
    assert store.save_records([first, retry]) == 0
    assert [record.status for record in store.get_records("R1")] == ["FAIL", "PASS"]


def test_sqlite_migrates_legacy_schema_without_losing_records(tmp_path):
    db_path = tmp_path / "legacy.sqlite"
    record = _record("OLD", "PASS")
    with sqlite3.connect(db_path) as connection:
        connection.execute("""
            CREATE TABLE test_records (
                id INTEGER PRIMARY KEY, timestamp TEXT NOT NULL, run_id TEXT NOT NULL,
                device_id TEXT NOT NULL, test_name TEXT NOT NULL, status TEXT NOT NULL,
                temperature_c REAL, voltage_v REAL, frequency_mhz REAL,
                duration_ms REAL, error_code TEXT, message TEXT,
                extra_json TEXT NOT NULL DEFAULT '{}',
                UNIQUE(timestamp, run_id, device_id, test_name)
            )
        """)
        connection.execute("""
            INSERT INTO test_records
            (timestamp, run_id, device_id, test_name, status, temperature_c,
             voltage_v, frequency_mhz, duration_ms, error_code, message, extra_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (record.timestamp.isoformat(), record.run_id, record.device_id,
              record.test_name, record.status, record.temperature_c, None, None,
              None, None, None, "{}"))
    store = SQLiteRecordStore(db_path)
    assert store.get_records("OLD") == [record]


def test_regression_comparison_flags_drop_and_reports_new_tests():
    records = [_record("BASE", "PASS"), _record("BASE", "PASS"),
               _record("CAND", "FAIL"), _record("CAND", "PASS")]
    records.append(HardwareRecord(datetime(2026, 10, 20, tzinfo=timezone.utc),
                              "CAND", "D1", "memory_bist", "FAIL"))
    result = compare_runs(build_dataframe(records), "BASE", "CAND")
    assert result["regressions"] == ["cpu_stress"]
    assert result["by_test"]["cpu_stress"]["delta"] == -0.5
    assert result["by_test"]["memory_bist"]["delta"] is None


def test_regression_comparison_requires_both_runs():
    frame = build_dataframe([_record("BASE", "PASS")])
    try:
        compare_runs(frame, "BASE", "MISSING")
    except ValueError as exc:
        assert "MISSING" in str(exc)
    else:
        raise AssertionError("expected missing-run ValueError")
