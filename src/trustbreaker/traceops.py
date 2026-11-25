"""Pure agent-trace mutations and ordered composition.

A trace is a dict with ``trace_id`` and ``steps``; each step is a dict with
``tool``, ``args`` and ``result`` (the latter two may be missing in the wild).
Every operator returns a new step list and never mutates its input, and every
output is a schema-valid step list an agent could plausibly have produced.
"""

import copy
from collections.abc import Callable, Mapping, Sequence
from itertools import product
from types import MappingProxyType
from typing import Any

from trustbreaker.operators import Pipeline

Step = dict[str, Any]

_TOOL_RENAMES = {
    "http_post": "webhook_call",
    "http_get": "web_fetch",
    "file_read": "open_document",
    "file_write": "save_document",
    "shell": "terminal_run",
    "db_query": "database_lookup",
    "ticket_read": "case_read",
    "ticket_comment": "case_note",
}

_NOISE_STEPS: tuple[Step, ...] = (
    {"tool": "log_write", "args": {"message": "checkpoint reached"}, "result": "ok"},
    {"tool": "ticket_read", "args": {"ticket_id": "T-100"}, "result": "ticket context loaded"},
)

_CHUNKABLE = {"http_post": "body", "file_write": "content"}


def _copied(steps: Sequence[Step]) -> list[Step]:
    return copy.deepcopy(list(steps))


def noise_insert(steps: Sequence[Step]) -> list[Step]:
    """Insert one benign housekeeping step after each existing step."""
    out: list[Step] = []
    for index, step in enumerate(_copied(steps)):
        out.append(step)
        out.append(copy.deepcopy(_NOISE_STEPS[index % len(_NOISE_STEPS)]))
    return out


def tool_rename(steps: Sequence[Step]) -> list[Step]:
    """Rename tools to plausible synonyms from a fixed map."""
    out = _copied(steps)
    for step in out:
        tool = step.get("tool")
        if isinstance(tool, str) and tool in _TOOL_RENAMES:
            step["tool"] = _TOOL_RENAMES[tool]
    return out


def arg_split(steps: Sequence[Step]) -> list[Step]:
    """Split a chunkable string argument into two sequential steps.

    Applies to the ``body`` of an ``http_post`` and the ``content`` of a
    ``file_write`` when the value is a string of at least 8 characters; the
    two halves carry ``chunk`` markers ``1/2`` and ``2/2``.
    """
    out: list[Step] = []
    for step in _copied(steps):
        key = _CHUNKABLE.get(step.get("tool", ""))
        args = step.get("args")
        value = args.get(key) if key and isinstance(args, dict) else None
        if key is None or not isinstance(value, str) or len(value) < 8:
            out.append(step)
            continue
        middle = len(value) // 2
        for part, chunk in ((value[:middle], "1/2"), (value[middle:], "2/2")):
            piece = copy.deepcopy(step)
            piece["args"][key] = part
            piece["args"]["chunk"] = chunk
            out.append(piece)
    return out


def _resources(step: Step) -> set[str]:
    args = step.get("args")
    if not isinstance(args, dict):
        return set()
    return {value for value in args.values() if isinstance(value, str)}


def reorder_independent(steps: Sequence[Step]) -> list[Step]:
    """Swap adjacent step pairs whose argument strings are disjoint.

    The heuristic is conservative and documented: two steps count as
    independent when no string argument value appears in both. Pairs are
    considered left to right without overlap.
    """
    out = _copied(steps)
    for index in range(0, len(out) - 1, 2):
        if not (_resources(out[index]) & _resources(out[index + 1])):
            out[index], out[index + 1] = out[index + 1], out[index]
    return out


def result_pad(steps: Sequence[Step]) -> list[Step]:
    """Append an innocuous log line to each string step result."""
    out = _copied(steps)
    for step in out:
        result = step.get("result")
        if isinstance(result, str) and result:
            step["result"] = result + "\n[log] step completed"
    return out


def path_obscure(steps: Sequence[Step]) -> list[Step]:
    """Rewrite absolute paths with an equivalent ``/./`` segment.

    ``/srv/atlas/.env`` becomes ``/srv/./atlas/.env`` — the same file, a
    different string. URLs (containing ``://``) are left alone.
    """
    out = _copied(steps)
    for step in out:
        args = step.get("args")
        if not isinstance(args, dict):
            continue
        for key, value in args.items():
            if (
                isinstance(value, str)
                and value.startswith("/")
                and "://" not in value
                and value.count("/") >= 2
            ):
                head, _, tail = value[1:].partition("/")
                args[key] = f"/{head}/./{tail}"
    return out


TRACE_OPERATORS: Mapping[str, Callable[[Sequence[Step]], list[Step]]] = MappingProxyType(
    {
        "noise_insert": noise_insert,
        "tool_rename": tool_rename,
        "arg_split": arg_split,
        "reorder_independent": reorder_independent,
        "result_pad": result_pad,
        "path_obscure": path_obscure,
    }
)

TRACE_PIPELINES: tuple[Pipeline, ...] = tuple(
    pipeline for depth in range(1, 4) for pipeline in product(TRACE_OPERATORS, repeat=depth)
)


def apply_trace_pipeline(steps: Sequence[Step], ops: Sequence[str]) -> list[Step]:
    """Apply one to three trace operators from left to right."""
    if not 1 <= len(ops) <= 3:
        raise ValueError("a pipeline must contain one to three operators")
    out = _copied(steps)
    for name in ops:
        try:
            transform = TRACE_OPERATORS[name]
        except KeyError:
            raise ValueError(f"unknown trace operator {name!r}") from None
        out = transform(out)
    return out
