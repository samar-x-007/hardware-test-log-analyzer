"""Command-line entry point."""
import argparse
import json
from .analysis import build_dataframe, summarize
from .parser import parse_file
from .regression import compare_runs
from .storage import SQLiteRecordStore


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize hardware validation log files")
    parser.add_argument("logs", nargs="+", help="log files to parse")
    parser.add_argument("--csv", help="optional path to save parsed rows as CSV")
    parser.add_argument("--db", help="optional SQLite database path for persistent records")
    parser.add_argument("--compare", nargs=2, metavar=("BASELINE", "CANDIDATE"),
                        help="compare per-test pass rates for two run IDs")
    args = parser.parse_args()
    records, errors = [], []
    for path in args.logs:
        parsed = parse_file(path)
        records.extend(parsed.records)
        errors.extend(f"{path}: {error}" for error in parsed.errors)
    frame = build_dataframe(records)
    if args.db:
        SQLiteRecordStore(args.db).save_records(records)
    if args.csv:
        frame.to_csv(args.csv, index=False)
    output = {"summary": summarize(frame)}
    if args.compare:
        output["comparison"] = compare_runs(frame, *args.compare)
    print(json.dumps(output, indent=2))
    if errors:
        print("\nParse issues:", *errors, sep="\n- ")

if __name__ == "__main__":
    main()
