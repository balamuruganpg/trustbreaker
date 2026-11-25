"""Generate trace mutations, measure bypasses, and aggregate observations."""

import json
from collections import Counter
from collections.abc import Iterable
from typing import Any

from trustbreaker.bandit import UCB1
from trustbreaker.results import ArmStats, BypassStats, VariantStatus
from trustbreaker.scanners import ScanResult, TraceScanner
from trustbreaker.trace_results import TraceAttackResult, TraceBreakReport, TraceVariantResult
from trustbreaker.traceops import TRACE_OPERATORS, TRACE_PIPELINES, apply_trace_pipeline


def _stats(applicable: int, bypasses: int) -> BypassStats:
    return BypassStats(applicable, bypasses, bypasses / applicable if applicable else None)


def _canonical(trace: dict[str, Any]) -> str:
    return json.dumps(trace, sort_keys=True, ensure_ascii=False, default=str)


class TraceBreaker:
    """Attack a trace scanner with mutated traces, UCB1-allocated."""

    def __init__(self, scanner: TraceScanner, budget_per_trace: int = 40, seed: int = 13) -> None:
        if budget_per_trace < 0:
            raise ValueError("budget must be non-negative")
        self._scanner = scanner
        self.budget_per_trace = budget_per_trace
        self.seed = seed
        self._bandit = UCB1(TRACE_PIPELINES, seed)

    def _scan(self, trace: dict[str, Any]) -> ScanResult:
        result = self._scanner.scan(trace)
        return ScanResult(flagged=result.flagged, score=float(result.score))

    @property
    def bandit(self) -> dict[str, ArmStats]:
        return self._bandit.snapshot()

    def attack_one(self, trace: dict[str, Any]) -> TraceAttackResult:
        original = self._scan(trace)
        steps = trace.get("steps")
        if not isinstance(steps, list):
            raise ValueError("a trace must carry a steps list")
        seen = {_canonical(trace)}
        candidates = list(TRACE_PIPELINES)
        variants: list[TraceVariantResult] = []
        while candidates and len(variants) < self.budget_per_trace:
            self._bandit.prioritize(candidates)
            mutated: dict[str, Any] | None = None
            pipeline: tuple[str, ...] = ()
            while candidates:
                pipeline = candidates.pop()
                candidate = dict(trace)
                candidate["steps"] = apply_trace_pipeline(steps, pipeline)
                if _canonical(candidate) not in seen:
                    mutated = candidate
                    break
            if mutated is None:
                break

            seen.add(_canonical(mutated))
            scan = self._scan(mutated)
            status: VariantStatus
            if not original.flagged:
                status = "not_applicable"
            elif scan.flagged:
                status = "detected"
            else:
                status = "bypassed"
            variant = TraceVariantResult(pipeline, mutated, scan, status)
            variants.append(variant)
            self._bandit.record(pipeline, variant.bypassed)

        trace_id = trace.get("trace_id")
        return TraceAttackResult(
            trace_id=trace_id if isinstance(trace_id, str) else "",
            original=original,
            variants=tuple(variants),
        )

    def attack(self, traces: Iterable[dict[str, Any]]) -> TraceBreakReport:
        """Start a seeded run and share its bandit across the supplied traces."""
        self._bandit = UCB1(TRACE_PIPELINES, self.seed)
        results = tuple(self.attack_one(trace) for trace in traces)
        operator_applicable: Counter[str] = Counter()
        operator_bypasses: Counter[str] = Counter()
        pipeline_applicable: Counter[str] = Counter()
        pipeline_bypasses: Counter[str] = Counter()
        for result in results:
            for variant in result.variants:
                name = "+".join(variant.pipeline)
                pipeline_applicable[name] += int(result.original.flagged)
                pipeline_bypasses[name] += int(variant.bypassed)
                for operator in dict.fromkeys(variant.pipeline):
                    operator_applicable[operator] += int(result.original.flagged)
                    operator_bypasses[operator] += int(variant.bypassed)

        overall = _stats(pipeline_applicable.total(), pipeline_bypasses.total())
        rate = overall.bypass_rate
        return TraceBreakReport(
            seed=self.seed,
            budget_per_trace=self.budget_per_trace,
            applicable_variants=overall.applicable,
            bypasses=overall.bypasses,
            bypass_rate=rate,
            robustness_score=1.0 - rate if rate is not None else None,
            per_operator={
                name: _stats(operator_applicable[name], operator_bypasses[name])
                for name in TRACE_OPERATORS
            },
            per_pipeline={
                name: _stats(pipeline_applicable[name], pipeline_bypasses[name])
                for name in sorted(pipeline_applicable)
            },
            results=results,
            bandit=self.bandit,
        )
