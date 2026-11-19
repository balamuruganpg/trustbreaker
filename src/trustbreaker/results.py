"""Structured results for individual attacks and benchmark runs."""

from dataclasses import dataclass
from typing import Literal

from trustbreaker.operators import Pipeline
from trustbreaker.scanners import ScanResult

VariantStatus = Literal["bypassed", "detected", "not_applicable"]


@dataclass(frozen=True, slots=True)
class VariantResult:
    pipeline: Pipeline
    text: str
    scan: ScanResult
    status: VariantStatus

    @property
    def bypassed(self) -> bool:
        return self.status == "bypassed"


@dataclass(frozen=True, slots=True)
class AttackResult:
    text: str
    original: ScanResult
    variants: tuple[VariantResult, ...]


@dataclass(frozen=True, slots=True)
class ArmStats:
    pulls: int
    successes: int
    ucb_score: float | None


@dataclass(frozen=True, slots=True)
class BypassStats:
    applicable: int
    bypasses: int
    bypass_rate: float | None


@dataclass(frozen=True, slots=True)
class BreakReport:
    seed: int
    budget_per_text: int
    applicable_variants: int
    bypasses: int
    bypass_rate: float | None
    robustness_score: float | None
    per_operator: dict[str, BypassStats]
    per_pipeline: dict[str, BypassStats]
    results: tuple[AttackResult, ...]
    bandit: dict[str, ArmStats]
