"""Typed data structures shared by ingestion and analysis layers."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class TestRecord:
    timestamp: datetime
    run_id: str
    device_id: str
    test_name: str
    status: str
    temperature_c: float | None = None
    voltage_v: float | None = None
    frequency_mhz: float | None = None
    duration_ms: float | None = None
    error_code: str | None = None
    message: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParseResult:
    records: list[TestRecord] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
