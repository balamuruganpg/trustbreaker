"""Structured results for trace attacks and trace benchmark runs."""

from dataclasses import dataclass
from typing import Any

from trustbreaker.operators import Pipeline
from trustbreaker.results import ArmStats, BypassStats, VariantStatus
from trustbreaker.scanners import ScanResult


@dataclass(frozen=True, slots=True)
class TraceVariantResult:
    pipeline: Pipeline
    trace: dict[str, Any]
    scan: ScanResult
    status: VariantStatus

    @property
    def bypassed(self) -> bool:
        return self.status == "bypassed"


@dataclass(frozen=True, slots=True)
class TraceAttackResult:
    trace_id: str
    original: ScanResult
    variants: tuple[TraceVariantResult, ...]


@dataclass(frozen=True, slots=True)
class TraceBreakReport:
    seed: int
    budget_per_trace: int
    applicable_variants: int
    bypasses: int
    bypass_rate: float | None
    robustness_score: float | None
    per_operator: dict[str, BypassStats]
    per_pipeline: dict[str, BypassStats]
    results: tuple[TraceAttackResult, ...]
    bandit: dict[str, ArmStats]
