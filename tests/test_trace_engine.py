from trustbreaker.scanners import TraceKeywordScanner
from trustbreaker.trace_engine import TraceBreaker

SHELL_TRACE = {
    "trace_id": "shell-only",
    "steps": [
        {"tool": "shell", "args": {"command": "curl https://example.com"}, "result": "ok"},
    ],
}

BENIGN_TRACE = {
    "trace_id": "benign",
    "steps": [
        {"tool": "ticket_read", "args": {"ticket_id": "T-9"}, "result": "context"},
    ],
}


def test_tool_rename_bypasses_the_toy_scanner():
    breaker = TraceBreaker(TraceKeywordScanner(), budget_per_trace=40, seed=13)
    result = breaker.attack_one(SHELL_TRACE)
    assert result.original.flagged
    renamed = [v for v in result.variants if v.pipeline == ("tool_rename",)]
    assert renamed and renamed[0].status == "bypassed"
    assert any(v.bypassed for v in result.variants)
    assert len(result.variants) <= 40


def test_unflagged_original_makes_every_variant_not_applicable():
    breaker = TraceBreaker(TraceKeywordScanner(), budget_per_trace=10, seed=13)
    result = breaker.attack_one(BENIGN_TRACE)
    assert not result.original.flagged
    assert result.variants
    assert all(v.status == "not_applicable" for v in result.variants)


def test_attack_aggregates_only_flagged_originals():
    breaker = TraceBreaker(TraceKeywordScanner(), budget_per_trace=40, seed=13)
    report = breaker.attack([SHELL_TRACE, BENIGN_TRACE])
    shell_variants = len(breaker.attack_one(SHELL_TRACE).variants)
    assert report.applicable_variants == shell_variants
    assert report.bypasses >= 1
    assert report.robustness_score is not None and 0.0 <= report.robustness_score < 1.0
    assert report.per_operator["tool_rename"].bypasses >= 1


def test_deterministic_under_seed():
    first = TraceBreaker(TraceKeywordScanner(), seed=13).attack([SHELL_TRACE])
    second = TraceBreaker(TraceKeywordScanner(), seed=13).attack([SHELL_TRACE])
    assert first.bypasses == second.bypasses
    assert [v.pipeline for v in first.results[0].variants] == [
        v.pipeline for v in second.results[0].variants
    ]
