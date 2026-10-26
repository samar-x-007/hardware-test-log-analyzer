# Hardware Test Log Analyzer Demo

## Before presenting

From the project folder in VS Code, open a terminal and run:

```bash
source .venv/bin/activate
streamlit run app.py
```

The dashboard opens in a browser using the bundled synthetic logs. No API key, external account, or hardware device is needed.

## Five-minute walkthrough

1. **Frame the problem:** validation logs are difficult to scan across devices and runs. This tool parses each row into structured records and produces local summaries.
2. **Show the overview:** point out total records, pass rate, failures/errors, and results grouped by test.
3. **Filter the data:** use the sidebar to choose `FAIL` and `ERROR`, then narrow by run, test, or device. Metrics and charts update with the selection.
4. **Compare runs:** restore both sample runs in the sidebar and show the baseline/candidate comparison, including tests with lower pass rates.
5. **Inspect trends and records:** show the temperature/voltage/frequency measurements in **Trends**, then show the filtered rows and CSV download in **Records**.
6. **Explain triage:** show a failure clue and emphasize that it is a transparent rule-based suggestion for follow-up checks, not a proven root cause.
7. **Show repeatability:** save the current records to SQLite history, switch to **Saved history**, and reload the run.

## Suggested narration

“This is a local hardware validation log analyzer. It parses key/value log lines, summarizes test outcomes, compares runs, and highlights failure clues with transparent rules. The included dataset is synthetic. The same workflow can be used with approved log files, and results can be exported for further analysis.”

## After the demo

Stop Streamlit with `Ctrl+C` in the terminal. To run the automated checks, use:

```bash
pytest
python scripts/evaluate_diagnosis.py
```
