"""Structural scanner interfaces and the built-in adapters."""

from collections.abc import Callable
from dataclasses import dataclass
from importlib import import_module
from typing import Protocol, runtime_checkable


class ScanLike(Protocol):
    @property
    def flagged(self) -> bool: ...

    @property
    def score(self) -> float: ...


@dataclass(frozen=True, slots=True)
class ScanResult:
    flagged: bool
    score: float


@runtime_checkable
class Scanner(Protocol):
    def scan(self, text: str, /) -> ScanLike: ...


ScannerInput = Scanner | Callable[[str], bool]


class KeywordScanner:
    """Demo scanner using case-insensitive substring matches."""

    keywords = ("ignore", "reveal", "instructions", "system prompt", "forget")

    def scan(self, text: str) -> ScanResult:
        lowered = text.casefold()
        flagged = any(keyword in lowered for keyword in self.keywords)
        return ScanResult(flagged=flagged, score=float(flagged))


class PromptWardenScanner:
    """Adapter for PromptWarden's default Warden and bundled model."""

    def __init__(self) -> None:
        try:
            warden_type: Callable[[], Scanner] = import_module("promptwarden").Warden
        except (ImportError, AttributeError) as error:
            raise ImportError("the promptwarden scanner requires promptwarden.Warden") from error
        self._warden = warden_type()

    def scan(self, text: str) -> ScanLike:
        return self._warden.scan(text)


@runtime_checkable
class TraceScanner(Protocol):
    def scan(self, trace: dict[str, object], /) -> ScanLike: ...


class TraceKeywordScanner:
    """Toy trace scanner: flags known-dangerous tools or secret-shaped args.

    Deliberately naive — it matches exact tool names and the substrings
    ``.env`` / ``secret`` in string arguments — so trace mutations have
    something honest to evade in demos and tests.
    """

    tools = ("http_post", "shell", "file_delete")
    markers = (".env", "secret")

    def scan(self, trace: dict[str, object]) -> ScanResult:
        steps = trace.get("steps")
        if not isinstance(steps, list):
            return ScanResult(flagged=False, score=0.0)
        for step in steps:
            if not isinstance(step, dict):
                continue
            if step.get("tool") in self.tools:
                return ScanResult(flagged=True, score=1.0)
            args = step.get("args")
            if isinstance(args, dict):
                for value in args.values():
                    if isinstance(value, str) and any(m in value.lower() for m in self.markers):
                        return ScanResult(flagged=True, score=1.0)
        return ScanResult(flagged=False, score=0.0)


class AgentSentinelScanner:
    """Adapter for AgentSentinel's default Sentinel and bundled model."""

    def __init__(self) -> None:
        try:
            sentinel_type: Callable[[], TraceScanner] = import_module("agentsentinel").Sentinel
        except (ImportError, AttributeError) as error:
            raise ImportError("trace scanning requires agentsentinel.Sentinel") from error
        self._sentinel = sentinel_type()

    def scan(self, trace: dict[str, object]) -> ScanLike:
        return self._sentinel.scan(trace)
