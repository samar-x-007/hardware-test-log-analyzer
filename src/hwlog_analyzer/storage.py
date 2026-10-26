"""SQLite persistence adapter for normalized validation records."""
import json
import hashlib
import sqlite3
from datetime import datetime
from pathlib import Path
from .models import TestRecord


class SQLiteRecordStore:
    """Store and retrieve parsed records without coupling parsing to SQLite."""

    def __init__(self, path: str | Path):
        self.path = str(path)
        with self._connect() as connection:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(test_records)")}
            if columns and "record_key" not in columns:
                # Migrate the first-milestone schema, whose narrower unique key
                # could collapse distinct attempts at the same timestamp.
                connection.execute("ALTER TABLE test_records RENAME TO test_records_legacy")
            connection.execute("""
                CREATE TABLE IF NOT EXISTS test_records (
                    id INTEGER PRIMARY KEY,
                    record_key TEXT NOT NULL UNIQUE,
                    timestamp TEXT NOT NULL,
                    run_id TEXT NOT NULL,
                    device_id TEXT NOT NULL,
                    test_name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    temperature_c REAL,
                    voltage_v REAL,
                    frequency_mhz REAL,
                    duration_ms REAL,
                    error_code TEXT,
                    message TEXT,
                    extra_json TEXT NOT NULL DEFAULT '{}'
                )
            """)
            legacy = connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test_records_legacy'"
            ).fetchone()
            if legacy:
                old_rows = connection.execute("""
                    SELECT timestamp, run_id, device_id, test_name, status,
                           temperature_c, voltage_v, frequency_mhz, duration_ms,
                           error_code, message, extra_json FROM test_records_legacy
                """).fetchall()
                self._insert_rows(connection, old_rows)
                connection.execute("DROP TABLE test_records_legacy")

    def _connect(self):
        return sqlite3.connect(self.path)

    def save_records(self, records: list[TestRecord]) -> int:
        """Insert records idempotently; return the number newly inserted."""
        rows = []
        for r in records:
            payload = (r.timestamp.isoformat(), r.run_id, r.device_id, r.test_name,
                       r.status, r.temperature_c, r.voltage_v, r.frequency_mhz,
                       r.duration_ms, r.error_code, r.message,
                       json.dumps(r.extra, sort_keys=True))
            record_key = hashlib.sha256(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
            rows.append((record_key, *payload))
        with self._connect() as connection:
            before = connection.total_changes
            self._insert_rows(connection, rows)
            return connection.total_changes - before

    @staticmethod
    def _insert_rows(connection: sqlite3.Connection, rows: list[tuple]) -> None:
        """Insert rows with a deterministic full-record key."""
        prepared = []
        for row in rows:
            if len(row) == 12:  # rows from the original schema migration
                payload = tuple(row)
                key = hashlib.sha256(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")).hexdigest()
                row = (key, *payload)
            prepared.append(row)
        connection.executemany("""
            INSERT OR IGNORE INTO test_records
            (record_key, timestamp, run_id, device_id, test_name, status,
             temperature_c, voltage_v, frequency_mhz, duration_ms, error_code,
             message, extra_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, prepared)

    def get_records(self, run_id: str | None = None) -> list[TestRecord]:
        """Load all records, or only records for a single run."""
        query = "SELECT timestamp, run_id, device_id, test_name, status, temperature_c, voltage_v, frequency_mhz, duration_ms, error_code, message, extra_json FROM test_records"
        params: tuple = ()
        if run_id is not None:
            query += " WHERE run_id = ?"
            params = (run_id,)
        query += " ORDER BY timestamp, run_id, device_id, test_name"
        with self._connect() as connection:
            rows = connection.execute(query, params).fetchall()
        return [TestRecord(datetime.fromisoformat(row[0]), *row[1:11], extra=json.loads(row[11])) for row in rows]

    def list_run_ids(self) -> list[str]:
        with self._connect() as connection:
            return [row[0] for row in connection.execute("SELECT DISTINCT run_id FROM test_records ORDER BY run_id")]
