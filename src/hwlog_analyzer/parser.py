"""Parser for the project's documented key=value validation log format."""
from datetime import datetime
import math
from pathlib import Path
import re
from .models import ParseResult, TestRecord

_PAIR = re.compile(r'([A-Za-z][A-Za-z0-9_]*)=("(?:[^"\\]|\\.)*"|\S+)')
_REQUIRED = {"ts", "run", "device", "test", "status"}
_FLOAT_FIELDS = {"temp_c": "temperature_c", "voltage_v": "voltage_v", "freq_mhz": "frequency_mhz", "duration_ms": "duration_ms"}
_KNOWN = _REQUIRED | set(_FLOAT_FIELDS) | {"error", "message"}


def parse_line(line: str, line_number: int | None = None) -> TestRecord:
    """Parse one log line; raise ValueError with a useful location on invalid input."""
    fields: dict[str, str] = {}
    for match in _PAIR.finditer(line):
        key, value = match.groups()
        key = key.lower()
        if key in fields:
            raise ValueError(f"duplicate field {key!r}")
        if value.startswith('"'):
            import json
            value = json.loads(value)
        fields[key] = value
    missing = _REQUIRED - fields.keys()
    if missing:
        raise ValueError(f"missing required fields: {', '.join(sorted(missing))}")
    try:
        timestamp = datetime.fromisoformat(fields["ts"].replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid timestamp {fields['ts']!r}") from exc
    status = fields["status"].upper()
    if status not in {"PASS", "FAIL", "ERROR", "SKIP"}:
        raise ValueError(f"unsupported status {fields['status']!r}")
    numbers: dict[str, float | None] = {}
    for source, target in _FLOAT_FIELDS.items():
        try:
            value = float(fields[source]) if source in fields else None
            if value is not None and not math.isfinite(value):
                raise ValueError(f"non-finite numeric value for {source}: {fields[source]!r}")
            numbers[target] = value
        except ValueError as exc:
            raise ValueError(f"invalid numeric value for {source}: {fields[source]!r}") from exc
    return TestRecord(timestamp, fields["run"], fields["device"], fields["test"], status,
                      **numbers, error_code=fields.get("error"), message=fields.get("message"),
                      extra={k: v for k, v in fields.items() if k not in _KNOWN})


def parse_text(text: str) -> ParseResult:
    """Parse all nonblank lines, retaining valid records and reporting bad lines."""
    result = ParseResult()
    for number, line in enumerate(text.splitlines(), 1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        try:
            result.records.append(parse_line(line))
        except (ValueError, TypeError) as exc:
            result.errors.append(f"line {number}: {exc}")
    return result


def parse_file(path: str | Path) -> ParseResult:
    """Read and parse a UTF-8 log file."""
    return parse_text(Path(path).read_text(encoding="utf-8"))
