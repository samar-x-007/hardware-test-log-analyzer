# Hardware Test Log Analyzer

A local Python application for parsing and analyzing simulated hardware and silicon validation logs. The sample data is synthetic and intended for learning or portfolio demonstrations; it is not Apple, vendor, or production silicon data.

## What it does

- Parses timestamped `key=value` test records and reports malformed lines without discarding valid records.
- Normalizes test status and measurements into typed Python records.
- Uses Pandas to summarize pass rates and failures overall, by test, and by device.
- Provides a CLI for JSON summaries and CSV export.
- Saves parsed records to SQLite and compares per-test pass rates between runs.
- Provides an interactive Streamlit dashboard with filters, measurement charts, run comparisons, CSV export, saved history, and transparent rule-based failure triage.
- Includes 50 balanced synthetic diagnosis cases and an offline evaluation report with per-class precision, recall, F1, and a confusion matrix.

All processing runs locally. The project does not require API keys or cloud services.

## Install and run

You can run the dashboard locally on macOS, Windows, or Linux. You need Python 3.10 or newer and Git. The commands below download the project from GitHub, create an isolated Python environment, install the project and dashboard dependencies, and start Streamlit.

### macOS or Linux

Open Terminal and run:

```bash
git clone https://github.com/samar-x-007/hardware-test-log-analyzer.git
cd hardware-test-log-analyzer
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e "[dev,dashboard]"
streamlit run app.py
```

### Windows (PowerShell)

Open PowerShell and run:

```powershell
git clone https://github.com/samar-x-007/hardware-test-log-analyzer.git
cd hardware-test-log-analyzer
py -3 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,dashboard]"
streamlit run app.py
```

Streamlit prints a local URL in the terminal (usually `http://localhost:8501`). Open that address in your browser. The dashboard starts with bundled synthetic sample logs; use **Upload** in the sidebar to analyze your own `.log` or `.txt` files.

### Start it again later

Open a terminal in the project folder, activate the environment, and start the app:

```bash
source .venv/bin/activate       # macOS/Linux
streamlit run app.py
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead. You only need to create the environment and install dependencies once per computer.

### Other command-line examples

From the project root with the environment activated:

```bash
hwlog-analyzer data/sample_logs/*.log
hwlog-analyzer data/sample_logs/validation_run_001.log --csv parsed.csv
hwlog-analyzer data/sample_logs/*.log --db runs.sqlite --compare R001 R002
python scripts/evaluate_diagnosis.py
```

## Demo walkthrough

See [`DEMO.md`](DEMO.md) for a short presentation flow. The bundled synthetic logs make the dashboard usable immediately: show the summary, filter down to failures, compare the two sample runs, inspect measurement trends and local triage clues, then download the filtered records as CSV.

For publishing through VS Code’s Source Control view, see [`GITHUB_SETUP.md`](GITHUB_SETUP.md). The repository includes a GitHub Actions workflow that runs tests on pushes and pull requests.

In the dashboard, upload logs under **Current logs**, review the parsed results, then choose **Save current records to SQLite history**. Switch the sidebar data source to **Saved history** to reload and compare saved runs later. The database is stored at `data/hardware_test_logs.sqlite3` and is excluded from version control. Identical records are ignored on repeat saves while distinct retry outcomes remain separate. Existing databases from the earlier milestone are migrated when opened.

Run the offline triage evaluation with:

```bash
python scripts/evaluate_diagnosis.py
```

The benchmark is synthetic and its score is a smoke check, not evidence of real-world accuracy. Use approved, labeled hardware data to assess performance for your intended environment.

## Log format

One record per line. Required fields are `ts`, `run`, `device`, `test`, and `status`. Supported statuses are `PASS`, `FAIL`, `ERROR`, and `SKIP`. Optional numeric fields are `temp_c`, `voltage_v`, `freq_mhz`, and `duration_ms`; `error`, `message`, and additional key-value fields are retained. Quote values containing spaces.

```text
ts=2026-10-20T09:00:01Z run=R001 device=SOC-A17-001 test=cpu_stress status=PASS temp_c=71.4 voltage_v=0.82 freq_mhz=3200 duration_ms=60000
```

## Project structure

- `src/hwlog_analyzer/models.py`: normalized record types
- `src/hwlog_analyzer/parser.py`: text and file parsing
- `src/hwlog_analyzer/analysis.py`: Pandas conversion and summaries
- `src/hwlog_analyzer/cli.py`: command-line interface
- `src/hwlog_analyzer/diagnosis.py`: transparent heuristic failure triage
- `src/hwlog_analyzer/evaluation.py`: classification metrics
- `app.py`: Streamlit dashboard
- `data/sample_logs/`: synthetic example runs
- `data/evaluation/`: balanced synthetic diagnosis examples
- `scripts/evaluate_diagnosis.py`: offline evaluation runner
- `tests/`: parser, analysis, storage, diagnosis, and evaluation tests
- `.github/workflows/tests.yml`: automated test run for GitHub pushes and pull requests
- `DEMO.md`: reproducible project presentation outline
- `GITHUB_SETUP.md`: steps to publish the workspace from VS Code

Diagnosis suggestions are rule-based clues, not verified root causes. Confirm them with traces, lab measurements, and domain review.

## Tests

```bash
pytest
```
