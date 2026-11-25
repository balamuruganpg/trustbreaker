"""Measure trace-mutation bypass against AgentSentinel on its eval corpus.

Writes aggregates only (counts and rates) to
``benchmarks/agentsentinel-mutation-summary.json``. Per-variant mutated
traces are never written anywhere: the full report exists only in memory
for the duration of the run.
"""

import json
from pathlib import Path

from trustbreaker import AgentSentinelScanner, TraceBreaker

BENCHMARK_DIR = Path(__file__).resolve().parent
CORPUS = BENCHMARK_DIR.parents[1] / "agentsentinel" / "evals" / "corpus.jsonl"
REPORT_PATH = BENCHMARK_DIR / "agentsentinel-mutation-summary.json"
BUDGET = 40
SEED = 13


def main() -> None:
    try:
        from agentsentinel import __version__
        from agentsentinel.corpus import read_corpus

        scanner = AgentSentinelScanner()
    except ImportError as error:
        raise SystemExit("Make AgentSentinel importable before running the benchmark.") from error

    try:
        rows = read_corpus(CORPUS)
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error

    report = TraceBreaker(scanner, budget_per_trace=BUDGET, seed=SEED).attack(
        [row.trace for row in rows]
    )
    flagged = sum(1 for result in report.results if result.original.flagged)
    summary = {
        "benchmark": "AgentSentinel trace-mutation bypass on its eval corpus",
        "corpus": "agentsentinel/evals/corpus.jsonl",
        "scanner": f"agentsentinel {__version__}",
        "protocol": f"budget {BUDGET} variants per trace, seed {SEED}, UCB1 over trace pipelines",
        "originals": len(rows),
        "originals_flagged": flagged,
        "applicable_variants": report.applicable_variants,
        "bypasses": report.bypasses,
        "bypass_rate": report.bypass_rate,
        "robustness_score": report.robustness_score,
        "per_operator": {
            name: {
                "applicable": stats.applicable,
                "bypasses": stats.bypasses,
                "bypass_rate": stats.bypass_rate,
            }
            for name, stats in report.per_operator.items()
        },
    }
    REPORT_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(
        f"Flagged originals: {flagged}/{len(rows)}; applicable variants "
        f"{report.applicable_variants}; bypasses {report.bypasses} "
        f"({report.bypass_rate:.2%}); robustness {report.robustness_score:.2%}"
    )
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
