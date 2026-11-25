import sys
from types import ModuleType

import pytest

from trustbreaker import AgentSentinelScanner, ScanResult


def test_agentsentinel_is_optional(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(sys.modules, "agentsentinel", None)

    with pytest.raises(ImportError, match=r"requires agentsentinel\.Sentinel"):
        AgentSentinelScanner()


def test_agentsentinel_scans_the_original_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    trace: dict[str, object] = {
        "trace_id": "fixture",
        "steps": [{"tool": "ticket_read", "args": {"ticket_id": 42}}],
    }
    report = ScanResult(flagged=False, score=0.25)

    class StubSentinel:
        def scan(self, received: dict[str, object]) -> ScanResult:
            assert received is trace
            return report

    module = ModuleType("agentsentinel")
    monkeypatch.setattr(module, "Sentinel", StubSentinel, raising=False)
    monkeypatch.setitem(sys.modules, "agentsentinel", module)

    assert AgentSentinelScanner().scan(trace) is report
