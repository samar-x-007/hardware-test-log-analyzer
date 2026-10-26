"""Compare run-level test outcomes to flag pass-rate regressions."""
import pandas as pd


def compare_runs(frame: pd.DataFrame, baseline_run: str, candidate_run: str) -> dict:
    """Compare per-test pass rates; negative delta means the candidate regressed."""
    subset = frame[frame["run_id"].isin([baseline_run, candidate_run])]
    present = set(subset["run_id"].dropna().astype(str))
    missing = {baseline_run, candidate_run} - present
    if missing:
        raise ValueError(f"run(s) not found: {', '.join(sorted(missing))}")
    rates = subset.assign(passed=subset["status"].eq("PASS")).groupby(
        ["run_id", "test_name"])["passed"].mean().unstack("run_id")
    tests = {}
    for test_name, row in rates.iterrows():
        base = row.get(baseline_run)
        candidate = row.get(candidate_run)
        if pd.isna(base) or pd.isna(candidate):
            tests[str(test_name)] = {"baseline_pass_rate": None if pd.isna(base) else float(base),
                                     "candidate_pass_rate": None if pd.isna(candidate) else float(candidate),
                                     "delta": None, "regression": False}
            continue
        delta = float(candidate - base)
        tests[str(test_name)] = {"baseline_pass_rate": float(base),
                                 "candidate_pass_rate": float(candidate),
                                 "delta": delta, "regression": delta < 0}
    return {"baseline_run": baseline_run, "candidate_run": candidate_run,
            "regressions": [name for name, value in tests.items() if value["regression"]],
            "by_test": tests}
