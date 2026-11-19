from math import log, sqrt

import pytest

from trustbreaker import ArmStats, Breaker, BypassStats, KeywordScanner, ScanResult


def test_bandit_learns_the_weak_operator_across_texts(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("trustbreaker.engine.PIPELINES", (("leet",), ("case_mix",)))

    def toy_scanner(text: str) -> bool:
        return text.casefold() == "a"

    texts = ["a"] * 80
    breaker = Breaker(toy_scanner, budget_per_text=1, seed=13)
    report = breaker.attack(texts)
    assert report == breaker.attack(texts)
    weak = report.bandit["leet"]
    strong = report.bandit["case_mix"]
    assert weak.pulls / len(texts) > 0.5
    assert weak.pulls + strong.pulls == len(texts)
    assert weak.successes == weak.pulls
    assert strong.successes == 0
    assert weak.ucb_score == 1 + sqrt(2 * log(len(texts)) / weak.pulls)
    assert strong.ucb_score == sqrt(2 * log(len(texts)) / strong.pulls)


def test_keyword_report_matches_hand_computed_outcomes() -> None:
    report = Breaker(KeywordScanner(), budget_per_text=5).attack(["ignore", "hello"])
    flagged, unflagged = report.results
    assert flagged.original == ScanResult(flagged=True, score=1.0)
    assert [(item.pipeline, item.text, item.status) for item in flagged.variants] == [
        (("case_mix",), "IgNoRe", "detected"),
        (("char_reverse",), "erongi", "bypassed"),
        (("b64_wrap",), "decode this base64: aWdub3Jl", "bypassed"),
        (("synonym",), "disregard", "bypassed"),
        (("zero_width",), "i\u200bg\u200bn\u200bo\u200br\u200be", "bypassed"),
    ]
    assert unflagged.original == ScanResult(flagged=False, score=0.0)
    assert len(unflagged.variants) == 5
    assert all(item.status == "not_applicable" and not item.bypassed for item in unflagged.variants)
    assert report.applicable_variants == 5
    assert report.bypasses == 4
    assert report.bypass_rate == 0.8
    assert report.robustness_score == pytest.approx(0.2)
    assert report.per_operator["case_mix"] == BypassStats(1, 0, 0.0)
    assert report.per_operator["synonym"] == BypassStats(1, 1, 1.0)
    assert report.per_operator["leet"] == BypassStats(0, 0, None)
    assert report.per_pipeline["synonym"] == BypassStats(1, 1, 1.0)
    assert report.per_pipeline["leet"] == BypassStats(0, 0, None)
    assert report.bandit["char_reverse"] == ArmStats(1, 1, 1 + sqrt(2 * log(10)))
    assert report.bandit["word_reverse"] == ArmStats(0, 0, None)
    assert sum(arm.pulls for arm in report.bandit.values()) == 10


def test_composed_pipeline_counts_each_operator_once(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("trustbreaker.engine.PIPELINES", (("leet", "case_mix", "leet"),))
    report = Breaker(KeywordScanner()).attack(["ignore"])
    assert report.results[0].variants[0].text == "1Gn0R3"
    assert report.per_pipeline == {"leet+case_mix+leet": BypassStats(1, 1, 1.0)}
    assert report.per_operator["leet"] == BypassStats(1, 1, 1.0)
    assert report.per_operator["case_mix"] == BypassStats(1, 1, 1.0)
    assert report.applicable_variants == report.bypasses == 1
    assert report.robustness_score == 0.0


def test_clean_original_can_generate_a_flagged_variant() -> None:
    report = Breaker(KeywordScanner()).attack(["prompt system"])
    reversed_words = next(
        variant for variant in report.results[0].variants if variant.text == "system prompt"
    )
    assert reversed_words.scan.flagged
    assert reversed_words.status == "not_applicable"
    assert report.applicable_variants == report.bypasses == 0
    assert report.bypass_rate is None
    assert report.robustness_score is None


def test_deduplication_excludes_no_ops_and_is_per_source_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "trustbreaker.engine.PIPELINES", (("word_reverse",), ("leet", "leet"), ("leet",))
    )
    calls: list[str] = []

    def scanner(text: str) -> bool:
        calls.append(text)
        return text == "a"

    breaker = Breaker(scanner, budget_per_text=10)
    first = breaker.attack_one("a")
    second = breaker.attack_one("a")
    assert calls == ["a", "4", "a", "4"]
    assert [variant.text for variant in first.variants] == ["4"]
    assert [variant.text for variant in second.variants] == ["4"]
    assert breaker.bandit["leet"].pulls == 1
    assert breaker.bandit["leet+leet"].pulls == 1
    assert breaker.bandit["word_reverse"].pulls == 0


def test_zero_budget_reports_original_only() -> None:
    breaker = Breaker(KeywordScanner(), budget_per_text=0)
    report = breaker.attack(["ignore"])
    assert report.results[0].original.flagged
    assert report.results[0].variants == ()
    assert report.robustness_score is None
    assert all(arm == ArmStats(0, 0, None) for arm in report.bandit.values())
    with pytest.raises(ValueError, match="non-negative"):
        Breaker(KeywordScanner(), budget_per_text=-1)
