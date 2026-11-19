"""Generate mutations, measure bypasses, and aggregate the observations."""

from collections import Counter
from collections.abc import Iterable

from trustbreaker.bandit import UCB1
from trustbreaker.operators import OPERATORS, PIPELINES, apply_pipeline
from trustbreaker.results import (
    ArmStats,
    AttackResult,
    BreakReport,
    BypassStats,
    VariantResult,
    VariantStatus,
)
from trustbreaker.scanners import Scanner, ScannerInput, ScanResult


def _stats(applicable: int, bypasses: int) -> BypassStats:
    return BypassStats(applicable, bypasses, bypasses / applicable if applicable else None)


class Breaker:
    def __init__(self, scanner: ScannerInput, budget_per_text: int = 40, seed: int = 13) -> None:
        if budget_per_text < 0:
            raise ValueError("budget must be non-negative")
        self._scanner = scanner
        self.budget_per_text = budget_per_text
        self.seed = seed
        self._bandit = UCB1(PIPELINES, seed)

    def _scan(self, text: str) -> ScanResult:
        if isinstance(self._scanner, Scanner):
            result = self._scanner.scan(text)
            return ScanResult(flagged=result.flagged, score=float(result.score))
        flagged = self._scanner(text)
        return ScanResult(flagged=flagged, score=float(flagged))

    @property
    def bandit(self) -> dict[str, ArmStats]:
        return self._bandit.snapshot()

    def attack_one(self, text: str) -> AttackResult:
        original = self._scan(text)
        seen = {text}
        candidates = list(PIPELINES)
        variants: list[VariantResult] = []
        while candidates and len(variants) < self.budget_per_text:
            self._bandit.prioritize(candidates)
            while candidates:
                pipeline = candidates.pop()
                mutated = apply_pipeline(text, pipeline)
                if mutated not in seen:
                    break
            else:
                break

            seen.add(mutated)
            scan = self._scan(mutated)
            status: VariantStatus
            if not original.flagged:
                status = "not_applicable"
            elif scan.flagged:
                status = "detected"
            else:
                status = "bypassed"
            variant = VariantResult(pipeline, mutated, scan, status)
            variants.append(variant)
            self._bandit.record(pipeline, variant.bypassed)

        return AttackResult(text, original, tuple(variants))

    def attack(self, texts: Iterable[str]) -> BreakReport:
        """Start a seeded run and share its bandit across the supplied texts."""
        self._bandit = UCB1(PIPELINES, self.seed)
        results = tuple(self.attack_one(text) for text in texts)
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
        return BreakReport(
            seed=self.seed,
            budget_per_text=self.budget_per_text,
            applicable_variants=overall.applicable,
            bypasses=overall.bypasses,
            bypass_rate=rate,
            robustness_score=1.0 - rate if rate is not None else None,
            per_operator={
                name: _stats(operator_applicable[name], operator_bypasses[name])
                for name in OPERATORS
            },
            per_pipeline={
                name: _stats(pipeline_applicable[name], pipeline_bypasses[name])
                for name in sorted(pipeline_applicable)
            },
            results=results,
            bandit=self.bandit,
        )
