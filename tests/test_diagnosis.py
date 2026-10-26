from datetime import datetime, timezone
import pytest
from hwlog_analyzer.diagnosis import diagnose_record, diagnose_records
from hwlog_analyzer.models import TestRecord as HardwareRecord


def _record(status="FAIL", **kwargs):
    values = dict(timestamp=datetime(2026, 10, 20, tzinfo=timezone.utc),
                  run_id="R1", device_id="D1", test_name="cpu_stress", status=status)
    values.update(kwargs)
    return HardwareRecord(**values)


@pytest.mark.parametrize("record, category", [
    (_record(error_code="THERMAL_THROTTLE", temperature_c=89.0), "thermal_or_throttling"),
    (_record(test_name="pcie_link", error_code="PCIE_TRAIN_TIMEOUT"), "pcie_link_training"),
    (_record(test_name="memory_bist", error_code="ECC_UNCORRECTABLE"), "memory_integrity"),
    (_record(test_name="voltage_margin", voltage_v=0.70), "low_supply_voltage"),
    (_record(message="unexpected signature"), "unclassified_failure"),
])
def test_failure_signatures_return_cautious_findings(record, category):
    finding = diagnose_record(record)
    assert finding is not None
    assert finding.category == category
    assert finding.confidence == "low"
    assert finding.evidence
    assert finding.suggested_checks


def test_pass_record_is_not_diagnosed():
    assert diagnose_record(_record(status="PASS")) is None


def test_diagnose_records_returns_only_failures_and_errors():
    findings = diagnose_records([_record(status="PASS"), _record(status="ERROR")])
    assert len(findings) == 1
