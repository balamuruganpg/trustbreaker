# TrustBreaker — SPEC v1

**An adversarial evasion harness for LLM guardrails.** TrustBreaker takes attacks a scanner already catches and systematically mutates them — leetspeak, spacing, homoglyphs, encodings, reversals — to measure how easily the guardrail can be bypassed, which mutation families do the damage, and how robust the scanner really is. It exists because the trustworthy-LLM-systems line (PromptWarden, AgentSentinel) measures *detection*; nothing in the line measured *evasion* — and PromptWarden v0.3.0's own benchmark left exactly this gap open (its remaining injection misses are broad transforms).

## Contract

- Package `trustbreaker`, Python ≥ 3.11, **standard library only**, fully typed, ruff + mypy strict clean.
- Deterministic: every run is seeded (default seed 13); same inputs + seed → identical report, byte for byte in the JSON summary fields.

## Mutation operators

Each operator is a pure `str -> str` transform with a stable name. v1 ships:

`leet` (a→4, e→3, i→1, o→0, s→5, t→7), `space_out` (insert spaces between characters of words ≥ 4 chars), `zero_width` (insert U+200B inside words), `homoglyph` (Latin→look-alike Cyrillic/Greek for a fixed map), `case_mix` (alternating case), `punct_split` (hyphens between characters), `char_reverse` (reverse each word's characters), `word_reverse` (reverse word order), `b64_wrap` (wrap the payload in a "decode this base64:" instruction carrying the base64 of the text), `diacritic` (add combining diacritics to vowels), `synonym` (fixed small map of instruction-word swaps, e.g. ignore→disregard, reveal→show, instructions→directions).

Operators compose into **pipelines** of depth 1–3 (e.g. `leet+space_out`). Duplicate/colliding variants are deduplicated per source text.

## Scanner protocol

A scanner is any object with `scan(text) -> ScanLike` where `ScanLike` exposes `flagged: bool` and `score: float` — or any plain callable `str -> bool`. Built-in adapters:

- `PromptWardenScanner` — wraps `promptwarden.Warden` when the package is importable.
- `KeywordScanner` — a deliberately naive substring scanner (fixed keyword list) that ships for demos and tests, so the harness is fully usable with zero external packages.

## Attack engine

`Breaker(scanner, budget_per_text=40, seed=13)`:

- `attack_one(text) -> AttackResult`: the original verdict, plus every generated variant (within budget) with its operator pipeline, mutated text, and whether it **bypassed** (original flagged AND variant not flagged; variants of unflagged originals are reported as `not_applicable`, never counted as bypasses).
- **Adaptive allocation (the learned component):** a UCB1 multi-armed bandit over operator pipelines allocates the mutation budget across texts — pipelines that produced bypasses get sampled more. Bandit state is part of the result (pulls, successes, UCB scores per arm) so a report shows *how* the budget was spent.
- `attack(texts) -> BreakReport`: per-operator and per-pipeline bypass rates, overall bypass rate, a **robustness score** `1 - bypass_rate` over applicable variants, and the full per-text results.

## CLI

- `trustbreaker mutate --text "..." --ops leet,space_out` → prints the variant(s).
- `trustbreaker run --scanner promptwarden|keyword --corpus attacks.jsonl --budget 40 --seed 13 --out report.json` → writes the JSON report and prints a summary table (per-family bypass rates + robustness score) to stdout. Exit 0 always on a completed measurement; exit 2 on usage errors.
- Corpus format: JSONL, one `{"text": ..., "label": "injection"}` per line. Ships with `attacks/seed.jsonl`: 12 short, obviously synthetic injection attacks written for this project.

## Honesty rules

- TrustBreaker **measures** scanners; it never trains on, tunes, or edits them. A bypass is reported with the exact mutated text so any claim is reproducible.
- The seed corpus is measurement data — it must never be folded into any scanner's training set from this repo.
- Reports distinguish "scanner did not flag the original" (excluded) from "variant bypassed" — the headline bypass rate is over applicable variants only.

## Tests

Operator unit tests (exact expected outputs on fixed strings, incl. Unicode safety: operators never corrupt surrogate pairs or drop characters silently — length invariants where the operator promises them), bandit tests (on a toy scanner with one known-weak operator, the bandit's pull share for that arm exceeds uniform after N rounds, deterministically under the seed), engine tests on `KeywordScanner` with hand-computed expected bypass outcomes, CLI smoke tests (mutate + run on the seed corpus produce a schema-valid report).

## AgentSentinel trace baseline

`TraceScanner` describes `scan(trace) -> ScanLike`, with `flagged` and `score` on
the report. `AgentSentinelScanner` loads `agentsentinel.Sentinel` on construction
and passes the trace through to the default scanner. It raises `ImportError` if
the optional scanner is unavailable.

`benchmarks/run_agentsentinel_corpus.py` reads AgentSentinel's eval JSONL using
its corpus loader. Each row wraps a `trace` object with a `label` and a
`category`. The trace contains `trace_id` and `steps`, with some corpus steps
omitting `args` or `result`. Only the original trace is submitted to the
scanner, and labels are used to group the resulting counts. The benchmark
uses the corpus for measurement and records aggregate counts only.

## Trace evasion (v0.2.0)

`TraceBreaker` mirrors `Breaker` for agent traces. A trace scanner exposes
`scan(trace) -> ScanLike`; `AgentSentinelScanner` adapts AgentSentinel and
`TraceKeywordScanner` is a deliberately naive toy (exact tool names plus
`.env`/`secret` argument substrings). Six trace operators in
`traceops.TRACE_OPERATORS` — `noise_insert`, `tool_rename`, `arg_split`,
`reorder_independent`, `result_pad`, `path_obscure` — map step lists to
schema-valid step lists and compose into pipelines of depth 1–3, allocated by
the same UCB1 bandit. A bypass is a variant of a flagged original that the
scanner no longer flags; variants of unflagged originals are
`not_applicable`. The `run-traces` CLI accepts corpora of bare traces or of
rows wrapping a `trace` object. Benchmarks against AgentSentinel's eval
corpus publish aggregates only; mutated trace payloads are never recorded.
