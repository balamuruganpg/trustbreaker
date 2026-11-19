import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from trustbreaker.operators import OPERATORS, PIPELINES, apply_pipeline

ROOT = Path(__file__).resolve().parents[1]


def cli(*args: str, cwd: Path = ROOT) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "trustbreaker", *args],
        cwd=cwd,
        env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
        capture_output=True,
        text=True,
        check=False,
    )


def test_mutate_cli() -> None:
    result = cli("mutate", "--text", "team up!", "--ops", "leet,space_out")
    assert (result.returncode, result.stdout, result.stderr) == (0, "7 3 4 m up!\n", "")


def test_run_cli_writes_reproducible_report(tmp_path: Path) -> None:
    corpus = ROOT / "attacks" / "seed.jsonl"
    args = ("run", "--scanner", "keyword", "--corpus", str(corpus))
    first = cli(*args, cwd=tmp_path)
    assert first.returncode == 0, first.stderr
    assert "Robustness score:" in first.stdout
    assert all(name in first.stdout for name in OPERATORS)
    report_data = (tmp_path / "report.json").read_bytes()
    second = cli(*args, "--budget", "40", "--seed", "13", "--out", "second.json", cwd=tmp_path)
    assert (second.returncode, second.stdout) == (0, first.stdout)
    assert report_data == (tmp_path / "second.json").read_bytes()

    report = json.loads(report_data)
    assert set(report) == {
        "seed",
        "budget_per_text",
        "applicable_variants",
        "bypasses",
        "bypass_rate",
        "robustness_score",
        "per_operator",
        "per_pipeline",
        "results",
        "bandit",
    }
    assert (report["seed"], report["budget_per_text"]) == (13, 40)
    assert report["bypass_rate"] == report["bypasses"] / report["applicable_variants"]
    assert report["robustness_score"] == 1 - report["bypass_rate"]
    assert set(report["per_operator"]) == set(OPERATORS)
    assert set(report["bandit"]) == {"+".join(arm) for arm in PIPELINES}
    records = [json.loads(line) for line in corpus.read_text(encoding="utf-8").splitlines()]
    assert len(records) == 12
    assert [attack["text"] for attack in report["results"]] == [
        record["text"] for record in records
    ]
    assert all(record["label"] == "injection" for record in records)

    for attack in report["results"]:
        assert set(attack) == {"text", "original", "variants"}
        assert attack["original"] == {"flagged": True, "score": 1.0}
        variants = attack["variants"]
        assert len({variant["text"] for variant in variants}) == len(variants) == 40
        for variant in variants:
            assert set(variant) == {"pipeline", "text", "scan", "status"}
            assert variant["text"] == apply_pipeline(attack["text"], variant["pipeline"])
            assert variant["text"] != attack["text"]
            assert variant["scan"] in (
                {"flagged": True, "score": 1.0},
                {"flagged": False, "score": 0.0},
            )
            assert variant["status"] == ("detected" if variant["scan"]["flagged"] else "bypassed")
            assert "+".join(variant["pipeline"]) in report["per_pipeline"]
    for stats in (*report["per_operator"].values(), *report["per_pipeline"].values()):
        assert set(stats) == {"applicable", "bypasses", "bypass_rate"}
        assert 0 <= stats["bypasses"] <= stats["applicable"]
        expected = stats["bypasses"] / stats["applicable"] if stats["applicable"] else None
        assert stats["bypass_rate"] == expected
    for arm in report["bandit"].values():
        assert set(arm) == {"pulls", "successes", "ucb_score"}
        assert 0 <= arm["successes"] <= arm["pulls"]
        assert (arm["ucb_score"] is None) == (arm["pulls"] == 0)
    assert sum(arm["pulls"] for arm in report["bandit"].values()) == report["applicable_variants"]
    assert sum(arm["successes"] for arm in report["bandit"].values()) == report["bypasses"]


@pytest.mark.parametrize(
    "args",
    [
        (),
        ("mutate", "--text", "example", "--ops", "nonexistent"),
        ("mutate", "--text", "example", "--ops", "leet,leet,leet,leet"),
        ("run", "--scanner", "nonexistent", "--corpus", "attacks/seed.jsonl"),
        ("run", "--scanner", "keyword", "--corpus", "attacks/seed.jsonl", "--budget", "-1"),
    ],
)
def test_invalid_usage_exits_two(args: tuple[str, ...]) -> None:
    result = cli(*args)
    assert result.returncode == 2
    assert "error:" in result.stderr


def test_invalid_corpus_row_exits_two(tmp_path: Path) -> None:
    corpus = tmp_path / "bad.jsonl"
    corpus.write_text('{"text":"ignore","label":"injection"}\n{"text":null}\n', encoding="utf-8")
    result = cli("run", "--scanner", "keyword", "--corpus", str(corpus), cwd=tmp_path)
    assert result.returncode == 2
    assert "bad.jsonl:2:" in result.stderr
    assert not (tmp_path / "report.json").exists()
