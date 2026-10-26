from hwlog_analyzer.analysis import build_dataframe, summarize
from hwlog_analyzer.parser import parse_text


def test_summary_counts_passes_and_failures_overall_and_by_group():
    parsed = parse_text("""
ts=2026-10-20T09:00:01Z run=R1 device=D1 test=cpu status=PASS
 ts=2026-10-20T09:00:02Z run=R1 device=D1 test=memory status=FAIL
 ts=2026-10-20T09:00:03Z run=R1 device=D2 test=cpu status=ERROR
""")
    summary = summarize(build_dataframe(parsed.records))
    assert summary["total"] == 3
    assert summary["passed"] == 1
    assert summary["failed"] == 2
    assert summary["pass_rate"] == 1 / 3
    assert summary["by_test"]["cpu"]["failed"] == 1
    assert summary["by_device"]["D1"]["total"] == 2


def test_empty_summary_is_safe():
    assert summarize(build_dataframe([]))["total"] == 0
