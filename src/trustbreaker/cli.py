"""Command-line interface for composing mutations and running measurements."""

import argparse
import json
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile

from trustbreaker.engine import Breaker
from trustbreaker.operators import apply_pipeline
from trustbreaker.results import BreakReport
from trustbreaker.scanners import (
    AgentSentinelScanner,
    KeywordScanner,
    PromptWardenScanner,
    TraceKeywordScanner,
)
from trustbreaker.trace_engine import TraceBreaker
from trustbreaker.trace_results import TraceBreakReport


def _load_corpus(path: Path) -> list[str]:
    texts: list[str] = []
    with path.open(encoding="utf-8") as corpus:
        for number, line in enumerate(corpus, 1):
            try:
                record: object = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{number}: {error.msg}") from error
            match record:
                case {"text": str(text), "label": "injection"}:
                    texts.append(text)
                case _:
                    raise ValueError(f"{path}:{number}: expected string text and injection label")
    return texts


def _load_trace_corpus(path: Path) -> list[dict[str, object]]:
    traces: list[dict[str, object]] = []
    with path.open(encoding="utf-8") as corpus:
        for number, line in enumerate(corpus, 1):
            if not line.strip():
                continue
            try:
                record: object = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{number}: {error.msg}") from error
            match record:
                case {"trace": dict(trace)}:
                    traces.append(trace)
                case dict() as bare if "trace_id" in bare and "steps" in bare:
                    traces.append(bare)
                case _:
                    raise ValueError(
                        f"{path}:{number}: expected a trace object or a row wrapping one"
                    )
    return traces


def _print_trace_summary(report: TraceBreakReport) -> None:
    print(f"{'Operator':<20} {'Applicable':>10} {'Bypasses':>8} {'Bypass rate':>12}")
    for name, stats in report.per_operator.items():
        print(
            f"{name:<20} {stats.applicable:>10} {stats.bypasses:>8}"
            f" {_percent(stats.bypass_rate):>12}"
        )
    print(
        f"{'Overall':<20} {report.applicable_variants:>10} {report.bypasses:>8}"
        f" {_percent(report.bypass_rate):>12}"
    )
    print(f"Robustness score: {_percent(report.robustness_score)}")


def _write_report(path: Path, report: BreakReport | TraceBreakReport) -> None:
    payload = json.dumps(asdict(report), indent=2, allow_nan=False) + "\n"
    with NamedTemporaryFile(
        mode="w", encoding="utf-8", newline="\n", dir=path.parent, delete=False
    ) as output:
        temporary = Path(output.name)
        try:
            output.write(payload)
            output.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def _percent(rate: float | None) -> str:
    return "n/a" if rate is None else f"{rate:.2%}"


def _print_summary(report: BreakReport) -> None:
    print(f"{'Operator':<14} {'Applicable':>10} {'Bypasses':>8} {'Bypass rate':>12}")
    for name, stats in report.per_operator.items():
        print(
            f"{name:<14} {stats.applicable:>10} {stats.bypasses:>8}"
            f" {_percent(stats.bypass_rate):>12}"
        )
    print(
        f"{'Overall':<14} {report.applicable_variants:>10} {report.bypasses:>8}"
        f" {_percent(report.bypass_rate):>12}"
    )
    print(f"Robustness score: {_percent(report.robustness_score)}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="trustbreaker")
    commands = parser.add_subparsers(dest="command", required=True)
    mutate = commands.add_parser("mutate", help="apply a mutation pipeline")
    mutate.add_argument("--text", required=True)
    mutate.add_argument("--ops", required=True, help="comma-separated operator names")
    run = commands.add_parser("run", help="measure a scanner against a JSONL corpus")
    run.add_argument("--scanner", required=True, choices=("promptwarden", "keyword"))
    run.add_argument("--corpus", required=True, type=Path)
    run.add_argument("--budget", type=int, default=40)
    run.add_argument("--seed", type=int, default=13)
    run.add_argument("--out", type=Path, default=Path("report.json"))
    run_traces = commands.add_parser("run-traces", help="measure a trace scanner against a corpus")
    run_traces.add_argument("--scanner", required=True, choices=("agentsentinel", "trace-keyword"))
    run_traces.add_argument("--corpus", required=True, type=Path)
    run_traces.add_argument("--budget", type=int, default=40)
    run_traces.add_argument("--seed", type=int, default=13)
    run_traces.add_argument("--out", type=Path, default=Path("trace-report.json"))
    args = parser.parse_args(argv)

    if args.command == "mutate":
        try:
            variant = apply_pipeline(args.text, [name.strip() for name in args.ops.split(",")])
        except ValueError as error:
            mutate.error(str(error))
        print(variant)
        return 0

    if args.command == "run-traces":
        try:
            traces = _load_trace_corpus(args.corpus)
            trace_scanner = (
                AgentSentinelScanner() if args.scanner == "agentsentinel" else TraceKeywordScanner()
            )
            trace_breaker = TraceBreaker(
                trace_scanner, budget_per_trace=args.budget, seed=args.seed
            )
        except (ImportError, OSError, ValueError) as error:
            run_traces.error(str(error))
        trace_report = trace_breaker.attack(traces)
        try:
            _write_report(args.out, trace_report)
        except OSError as error:
            run_traces.error(str(error))
        _print_trace_summary(trace_report)
        return 0

    try:
        texts = _load_corpus(args.corpus)
        scanner = PromptWardenScanner() if args.scanner == "promptwarden" else KeywordScanner()
        breaker = Breaker(scanner, budget_per_text=args.budget, seed=args.seed)
    except (ImportError, OSError, ValueError) as error:
        run.error(str(error))
    report = breaker.attack(texts)
    try:
        _write_report(args.out, report)
    except OSError as error:
        run.error(str(error))
    _print_summary(report)
    return 0
