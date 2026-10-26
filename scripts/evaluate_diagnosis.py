"""Evaluate local rule-based triage against labeled synthetic examples."""
import json
from pathlib import Path

from hwlog_analyzer.diagnosis import diagnose_records
from hwlog_analyzer.evaluation import score_categories
from hwlog_analyzer.parser import parse_text


def main() -> None:
    path = Path(__file__).resolve().parents[1] / "data" / "evaluation" / "diagnosis_cases.jsonl"
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    records = []
    for case in cases:
        parsed = parse_text(case["log"])
        if len(parsed.records) != 1 or parsed.errors:
            raise ValueError(f"Invalid evaluation case {case['id']}: {parsed.errors}")
        records.append(parsed.records[0])

    findings = diagnose_records(records)
    if len(findings) != len(cases):
        raise ValueError("Expected exactly one rule-based finding per evaluation case")
    labels = sorted({case["expected"] for case in cases})
    expected = [case["expected"] for case in cases]
    predicted = [finding.category for finding in findings]
    report = score_categories(expected, predicted, labels)
    print("Offline rule-based triage evaluation (synthetic cases)")
    print(f"Accuracy: {report['accuracy']:.1%}  |  Macro F1: {report['macro_f1']:.3f}")
    print("Per-class metrics:")
    for label, values in report["per_class"].items():
        print(f"  {label}: precision={values['precision']:.2f} recall={values['recall']:.2f} "
              f"F1={values['f1']:.2f} support={values['support']}")
    print("Confusion matrix (rows=expected, columns=predicted):")
    print(json.dumps(report["confusion_matrix"], indent=2))
    for case, guess in zip(cases, predicted):
        marker = "✓" if guess == case["expected"] else "✗"
        print(f"{marker} {case['id']}: expected={case['expected']} predicted={guess}")


if __name__ == "__main__":
    main()
