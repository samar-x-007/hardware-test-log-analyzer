"""Pandas-based analysis, kept separate from parsing for future storage/UI layers."""
import pandas as pd
from .models import TestRecord


def build_dataframe(records: list[TestRecord]) -> pd.DataFrame:
    """Convert records into a consistently typed tabular dataset."""
    columns = ["timestamp", "run_id", "device_id", "test_name", "status", "temperature_c", "voltage_v", "frequency_mhz", "duration_ms", "error_code", "message"]
    rows = [{"timestamp": r.timestamp, "run_id": r.run_id, "device_id": r.device_id,
             "test_name": r.test_name, "status": r.status, "temperature_c": r.temperature_c,
             "voltage_v": r.voltage_v, "frequency_mhz": r.frequency_mhz,
             "duration_ms": r.duration_ms, "error_code": r.error_code, "message": r.message,
             **{f"extra_{k}": v for k, v in r.extra.items()}} for r in records]
    frame = pd.DataFrame(rows)
    for col in columns:
        if col not in frame:
            frame[col] = pd.Series(dtype="object")
    return frame[columns + sorted(c for c in frame.columns if c.startswith("extra_"))]


def summarize(frame: pd.DataFrame) -> dict:
    """Return overall, per-test and per-device pass rates and failure counts."""
    if frame.empty:
        return {"total": 0, "passed": 0, "failed": 0, "pass_rate": 0.0,
                "by_test": {}, "by_device": {}}
    passing = frame["status"].eq("PASS")
    def groups(column: str) -> dict:
        result = {}
        for key, group in frame.groupby(column, dropna=False):
            result[str(key)] = {"total": int(len(group)),
                                "passed": int(group["status"].eq("PASS").sum()),
                                "failed": int(group["status"].isin(["FAIL", "ERROR"]).sum()),
                                "pass_rate": float(group["status"].eq("PASS").mean())}
        return result
    return {"total": int(len(frame)), "passed": int(passing.sum()),
            "failed": int(frame["status"].isin(["FAIL", "ERROR"]).sum()),
            "pass_rate": float(passing.mean()), "by_test": groups("test_name"),
            "by_device": groups("device_id")}
