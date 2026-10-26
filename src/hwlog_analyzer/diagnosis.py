"""Transparent, heuristic triage hints for failed validation records."""
from dataclasses import asdict, dataclass
from .models import TestRecord


@dataclass(frozen=True)
class DiagnosisFinding:
    run_id: str
    device_id: str
    test_name: str
    error_code: str | None
    category: str
    evidence: str
    suggested_checks: tuple[str, ...]
    confidence: str = "low"

    def to_dict(self) -> dict:
        return asdict(self)


def diagnose_record(record: TestRecord) -> DiagnosisFinding | None:
    """Return a cautious triage hint for a failure/error, not a proven root cause."""
    if record.status not in {"FAIL", "ERROR"}:
        return None
    code = (record.error_code or "").upper()
    message = (record.message or "").lower()
    test = record.test_name.lower()
    if any(token in code for token in ("THERMAL", "OVER_TEMP")) or (record.temperature_c is not None and record.temperature_c >= 85):
        category = "thermal_or_throttling"
        evidence = f"Failure at {record.temperature_c:.1f} C" if record.temperature_c is not None else f"Error code {code}"
        checks = ("Check thermal limits, airflow, and sensor calibration.", "Compare frequency and temperature traces around the failure.")
    elif any(token in code for token in ("PCIE", "LINK_TRAIN")) or ("pcie" in test and "timeout" in message):
        category, evidence = "pcie_link_training", f"PCIe link training or timeout indicator ({code or record.message or test})"
        checks = ("Inspect link training state and negotiated width/speed.", "Check board, lane, and retimer configuration.")
    elif any(token in code for token in ("ECC", "MEMORY", "DRAM")) or ("memory" in test and any(w in message for w in ("ecc", "memory"))):
        category, evidence = "memory_integrity", f"Memory/ECC indicator ({code or record.message or test})"
        checks = ("Review ECC syndrome and failing address details.", "Repeat memory diagnostics across devices and operating corners.")
    elif record.voltage_v is not None and record.voltage_v < 0.75:
        category, evidence = "low_supply_voltage", f"Recorded supply {record.voltage_v:.3f} V"
        checks = ("Verify supply rail measurement at the device.", "Check droop during the failing test window.")
    else:
        category, evidence = "unclassified_failure", record.message or code or "Failure record has no recognized signature"
        checks = ("Review the full test trace and correlate with neighboring records.", "Compare against a known-good device and run.")
    return DiagnosisFinding(record.run_id, record.device_id, record.test_name, record.error_code, category, evidence, checks)


def diagnose_records(records: list[TestRecord]) -> list[DiagnosisFinding]:
    return [finding for record in records if (finding := diagnose_record(record)) is not None]
