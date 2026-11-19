"""Measure AgentSentinel's detection of original eval corpus traces."""

import json
from collections import Counter
from pathlib import Path

from trustbreaker import AgentSentinelScanner

BENCHMARK_DIR = Path(__file__).resolve().parent
CORPUS = BENCHMARK_DIR.parents[1] / "agentsentinel" / "evals" / "corpus.jsonl"
REPORT_PATH = BENCHMARK_DIR / "agentsentinel-corpus-summary.json"


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

    counts = Counter((row.label, scanner.scan(row.trace).flagged) for row in rows)
    malicious_flagged = counts["malicious", True]
    benign_flagged = counts["benign", True]
    originals_flagged = malicious_flagged + benign_flagged
    report = {
        "benchmark": "AgentSentinel original-trace detection on its eval corpus",
        "corpus": "agentsentinel/evals/corpus.jsonl",
        "scanner": f"agentsentinel {__version__}",
        "originals": len(rows),
        "originals_flagged": originals_flagged,
        "malicious_originals": malicious_flagged + counts["malicious", False],
        "malicious_originals_flagged": malicious_flagged,
        "benign_originals": benign_flagged + counts["benign", False],
        "benign_originals_flagged": benign_flagged,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Flagged {originals_flagged} of {len(rows)} original traces from {CORPUS}")
    print(f"Wrote {REPORT_PATH}")


if __name__ == "__main__":
    main()
