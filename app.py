"""Interactive Streamlit dashboard for hardware validation log analysis."""
from pathlib import Path

import pandas as pd
import streamlit as st

from hwlog_analyzer.analysis import build_dataframe, summarize
from hwlog_analyzer.diagnosis import diagnose_records
from hwlog_analyzer.parser import parse_file, parse_text
from hwlog_analyzer.regression import compare_runs
from hwlog_analyzer.storage import SQLiteRecordStore


ROOT = Path(__file__).parent
DATABASE = ROOT / "data" / "hardware_test_logs.sqlite3"


def _current_records(uploads):
    records, errors = [], []
    if uploads:
        sources = ((upload.name, upload.getvalue().decode("utf-8", errors="replace")) for upload in uploads)
        for name, text in sources:
            parsed = parse_text(text)
            records.extend(parsed.records)
            errors.extend(f"{name}: {issue}" for issue in parsed.errors)
    else:
        sample_dir = ROOT / "data" / "sample_logs"
        for path in sorted(sample_dir.glob("*.log")):
            parsed = parse_file(path)
            records.extend(parsed.records)
            errors.extend(f"{path.name}: {issue}" for issue in parsed.errors)
    return records, errors


def main() -> None:
    st.set_page_config(page_title="Hardware Test Log Analyzer", page_icon="🔧", layout="wide")
    st.title("Hardware Test Log Analyzer")
    st.caption("Explore validation runs, compare test outcomes, and inspect rule-based failure clues. Bundled logs are synthetic demo data.")

    store = SQLiteRecordStore(DATABASE)
    uploads = st.sidebar.file_uploader("Upload .log or .txt files", type=["log", "txt"], accept_multiple_files=True)
    mode = st.sidebar.radio("Data source", ["Current logs", "Saved history"])
    current_records, errors = _current_records(uploads)

    if mode == "Current logs":
        records = current_records
        if not uploads:
            st.sidebar.caption("Using bundled sample runs. Upload your own logs to explore them.")
        if records and st.sidebar.button("Save these records to history", width="stretch"):
            inserted = store.save_records(records)
            st.sidebar.success(f"Saved {inserted}; skipped {len(records) - inserted} duplicates.")
    else:
        saved_runs = store.list_run_ids()
        if not saved_runs:
            st.info("No saved runs yet. Switch to Current logs and save a run first.")
            return
        selected_runs = st.sidebar.multiselect("Saved runs", saved_runs, default=saved_runs)
        records = [record for run_id in selected_runs for record in store.get_records(run_id)]

    if errors:
        with st.expander(f"Parse issues ({len(errors)})"):
            st.warning("Valid lines are still included in the analysis.")
            st.write(errors)
    if not records:
        st.info("No records match this data selection.")
        return

    full_frame = build_dataframe(records)
    st.sidebar.subheader("Explore records")
    selected_statuses = st.sidebar.multiselect("Status", sorted(full_frame["status"].dropna().unique()), default=sorted(full_frame["status"].dropna().unique()))
    selected_tests = st.sidebar.multiselect("Test", sorted(full_frame["test_name"].dropna().unique()), default=sorted(full_frame["test_name"].dropna().unique()))
    selected_devices = st.sidebar.multiselect("Device", sorted(full_frame["device_id"].dropna().unique()), default=sorted(full_frame["device_id"].dropna().unique()))
    selected_runs = st.sidebar.multiselect("Run", sorted(full_frame["run_id"].dropna().unique()), default=sorted(full_frame["run_id"].dropna().unique()))

    mask = (
        full_frame["status"].isin(selected_statuses)
        & full_frame["test_name"].isin(selected_tests)
        & full_frame["device_id"].isin(selected_devices)
        & full_frame["run_id"].isin(selected_runs)
    )
    frame = full_frame.loc[mask].copy()
    filtered_records = [record for record, include in zip(records, mask.tolist()) if include]
    summary = summarize(frame)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Records", summary["total"])
    c2.metric("Pass rate", f"{summary['pass_rate']:.1%}")
    c3.metric("Failures / errors", summary["failed"])
    c4.metric("Runs", frame["run_id"].nunique() if not frame.empty else 0)
    if frame.empty:
        st.warning("No records match the selected filters. Adjust the filters in the sidebar.")
        return

    overview_tab, trends_tab, records_tab, triage_tab = st.tabs(["Overview", "Trends", "Records", "Failure triage"])
    with overview_tab:
        st.subheader("Results by test")
        test_summary = pd.DataFrame.from_dict(summary["by_test"], orient="index").rename_axis("test")
        st.bar_chart(test_summary["pass_rate"], y_label="Pass rate")
        st.dataframe(test_summary, width="stretch")

        runs = sorted(frame["run_id"].dropna().unique().tolist())
        if len(runs) >= 2:
            st.subheader("Compare runs")
            left, right = st.columns(2)
            baseline = left.selectbox("Baseline", runs, index=0)
            candidate = right.selectbox("Candidate", [run for run in runs if run != baseline], index=0)
            comparison = compare_runs(frame, baseline, candidate)
            regressions = comparison["regressions"]
            if regressions:
                st.warning("Potential regressions: " + ", ".join(regressions))
            else:
                st.success("No pass-rate regressions detected for tests present in both runs.")
            comparison_frame = pd.DataFrame.from_dict(comparison["by_test"], orient="index").rename_axis("test")
            st.dataframe(comparison_frame, width="stretch")
            plot_columns = [column for column in (baseline, candidate) if column in comparison_frame]
            if plot_columns:
                st.bar_chart(comparison_frame[plot_columns], y_label="Pass rate")
        else:
            st.info("Select at least two runs in the sidebar to compare run performance.")

    with trends_tab:
        st.subheader("Measurement trends")
        numeric_columns = ["temperature_c", "voltage_v", "frequency_mhz", "duration_ms"]
        available = [column for column in numeric_columns if frame[column].notna().any()]
        chosen = st.multiselect("Measurements to plot", available, default=available[:2])
        if chosen:
            trend = frame.sort_values("timestamp").set_index("timestamp")[chosen]
            st.line_chart(trend, y_label="Recorded measurement")
        else:
            st.info("No numeric measurements match the selected filters.")
        st.subheader("Status counts")
        st.bar_chart(frame["status"].value_counts().sort_index(), y_label="Records")

    with records_tab:
        st.subheader("Filtered records")
        st.dataframe(frame.sort_values("timestamp", ascending=False), width="stretch", hide_index=True)
        st.download_button(
            "Download filtered CSV", frame.to_csv(index=False).encode("utf-8"),
            file_name="hardware_test_records.csv", mime="text/csv",
        )

    with triage_tab:
        st.subheader("Rule-based failure clues")
        findings = [finding.to_dict() for finding in diagnose_records(filtered_records)]
        if findings:
            st.caption("These rules suggest checks; they do not establish root cause. Confirm with traces and lab measurements.")
            st.dataframe(pd.DataFrame(findings), width="stretch", hide_index=True)
        else:
            st.success("No FAIL or ERROR records in this selection.")


if __name__ == "__main__":
    main()
