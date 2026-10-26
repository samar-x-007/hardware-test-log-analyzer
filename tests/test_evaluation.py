import json
from collections import Counter
from pathlib import Path

import pytest

from hwlog_analyzer.evaluation import score_categories
from hwlog_analyzer.parser import parse_text


def test_evaluation_reports_confusion_and_macro_f1():
    result = score_categories(["thermal", "pcie", "pcie"], ["thermal", "thermal", "pcie"], ["pcie", "thermal"])
    assert result["accuracy"] == pytest.approx(2 / 3)
    assert result["confusion_matrix"]["pcie"]["thermal"] == 1
    assert 0 <= result["macro_f1"] <= 1


def test_evaluation_rejects_inconsistent_or_unknown_labels():
    with pytest.raises(ValueError, match="counts must match"):
        score_categories(["thermal"], [], ["thermal"])
    with pytest.raises(ValueError, match="included"):
        score_categories(["thermal"], ["pcie"], ["thermal"])


def test_synthetic_evaluation_set_is_balanced_and_parseable():
    dataset = Path(__file__).resolve().parents[1] / "data/evaluation/diagnosis_cases.jsonl"
    cases = [json.loads(line) for line in dataset.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(cases) == 50
    assert len({case["id"] for case in cases}) == len(cases)
    assert set(Counter(case["expected"] for case in cases).values()) == {10}
    for case in cases:
        parsed = parse_text(case["log"])
        assert len(parsed.records) == 1, case["id"]
        assert not parsed.errors, case["id"]
        assert parsed.records[0].status in {"FAIL", "ERROR"}
