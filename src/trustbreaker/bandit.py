"""UCB1 over operator pipelines with reproducible tie-breaking."""

from collections import Counter
from math import inf, log, sqrt
from random import Random

from trustbreaker.operators import Pipeline
from trustbreaker.results import ArmStats


class UCB1:
    def __init__(self, pipelines: tuple[Pipeline, ...], seed: int) -> None:
        order = list(pipelines)
        Random(seed).shuffle(order)
        self._tie_break = {pipeline: index for index, pipeline in enumerate(order)}
        self._pulls: Counter[Pipeline] = Counter()
        self._successes: Counter[Pipeline] = Counter()
        self._total_pulls = 0

    def _score(self, pipeline: Pipeline, exploration: float) -> float:
        pulls = self._pulls[pipeline]
        if pulls == 0:
            return inf
        return self._successes[pipeline] / pulls + sqrt(exploration / pulls)

    def prioritize(self, candidates: list[Pipeline]) -> None:
        """Sort in place so the highest-priority pipeline is last."""
        exploration = 2 * log(max(1, self._total_pulls))
        candidates.sort(
            key=lambda pipeline: (
                self._score(pipeline, exploration),
                -len(pipeline),
                self._tie_break[pipeline],
            )
        )

    def record(self, pipeline: Pipeline, bypassed: bool) -> None:
        self._pulls[pipeline] += 1
        self._successes[pipeline] += int(bypassed)
        self._total_pulls += 1

    def snapshot(self) -> dict[str, ArmStats]:
        exploration = 2 * log(max(1, self._total_pulls))
        return {
            "+".join(pipeline): ArmStats(
                pulls=self._pulls[pipeline],
                successes=self._successes[pipeline],
                ucb_score=self._score(pipeline, exploration) if self._pulls[pipeline] else None,
            )
            for pipeline in sorted(self._tie_break)
        }
