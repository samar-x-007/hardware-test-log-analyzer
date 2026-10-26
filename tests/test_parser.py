from datetime import datetime, timezone
import pytest
from hwlog_analyzer.parser import parse_line, parse_text


def test_parses_record_and_preserves_extra_fields():
    record = parse_line('ts=2026-10-20T09:00:01Z run=R1 device=D1 test=cpu status=pass temp_c=71.5 custom=abc message="all good"')
    assert record.timestamp == datetime(2026, 10, 20, 9, 0, 1, tzinfo=timezone.utc)
    assert record.status == "PASS"
    assert record.temperature_c == 71.5
    assert record.message == "all good"
    assert record.extra == {"custom": "abc"}


@pytest.mark.parametrize("line, fragment", [
    ("run=R1 device=D1 test=cpu status=PASS", "missing required fields"),
    ("ts=nope run=R1 device=D1 test=cpu status=PASS", "invalid timestamp"),
    ("ts=2026-10-20T09:00:01Z run=R1 device=D1 test=cpu status=PASS temp_c=warm", "invalid numeric"),
    ("ts=2026-10-20T09:00:01Z run=R1 device=D1 test=cpu status=UNKNOWN", "unsupported status"),
])
def test_invalid_record_reports_clear_error(line, fragment):
    with pytest.raises(ValueError, match=fragment):
        parse_line(line)


def test_parse_text_keeps_valid_records_and_reports_bad_lines():
    result = parse_text("# comment\n\nts=2026-10-20T09:00:01Z run=R1 device=D1 test=cpu status=PASS\nnot a record")
    assert len(result.records) == 1
    assert result.errors == ["line 4: missing required fields: device, run, status, test, ts"]


def test_field_names_are_case_insensitive_and_duplicates_are_rejected():
    line = "ts=2026-10-20T09:00:01Z run=R1 device=D1 test=cpu status=PASS TS=2026-10-20T09:00:02Z"
    with pytest.raises(ValueError, match="duplicate field 'ts'"):
        parse_line(line)


@pytest.mark.parametrize("value", ["nan", "inf", "-inf"])
def test_non_finite_measurements_are_rejected(value):
    line = f"ts=2026-10-20T09:00:01Z run=R1 device=D1 test=cpu status=PASS temp_c={value}"
    with pytest.raises(ValueError, match="invalid numeric"):
        parse_line(line)


def test_empty_and_comment_only_text_is_valid_empty_input():
    result = parse_text("\n# simulated run\n  # another comment\n")
    assert result.records == []
    assert result.errors == []
