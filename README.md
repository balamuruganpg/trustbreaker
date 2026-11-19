# TrustBreaker

TrustBreaker measures how text mutations affect detection by an LLM guardrail.
It scans each original and its variants, records the exact text and verdict for
each scan, and summarizes bypass rates by operator and pipeline. The
implementation follows [SPEC.md](SPEC.md).

**88.28% of mutations bypass. Robustness is 11.72%.**

PromptWarden 0.3.0 on its own eval corpus: 2,613 of 2,960 applicable variants
bypassed, from 74 flagged originals out of 81 injection rows. Budget 40 per
text, seed 13. Source:
[promptwarden-corpus-summary.json](benchmarks/promptwarden-corpus-summary.json).

![Bypass rate by operator on the PromptWarden corpus: leet 98.47%, diacritic 97.77%, space_out 95.56%, punct_split 95.33%, word_reverse 93.66%, char_reverse 92.68%, b64_wrap 89.93%, synonym 82.00%, case_mix 81.73%, homoglyph 79.46%, zero_width 75.33%.](docs/assets/bypass-by-operator.svg)

*Per-operator bypass rate on that corpus. The red bar is the highest rate.*

![Robustness on the seed corpus: KeywordScanner 1.67%, PromptWarden 13.33%.](docs/assets/robustness.svg)

*Robustness on the seed corpus (`attacks/seed.jsonl`). This is a different run from the chart above.*

## How it works

### Allocation

Each arm is an ordered pipeline of up to three operators, with repetition
allowed. UCB1 takes the observed bypass fraction for an arm and adds an
exploration term that rises with the total number of pulls and falls as that
arm is sampled. Unpulled arms take priority. Ties favor shorter pipelines
and use a seeded order among pipelines of equal length. The bandit starts
fresh for each `Breaker.attack` run and carries observations from one text to
the next. Successive `attack_one` calls also share the current bandit.

The first pipeline to generate a distinct mutation gets credit for it.
Unchanged text and collisions consume no scan budget. Each variant scanned
is a pull, with a success only when the original was flagged and the variant
was clear. The report includes each arm's pulls, successes, and UCB score.
An unpulled arm has a `null` score in JSON. A run with fewer pulls than arms
can spend the full budget exploring.

### Operators

Word operators work on runs of alphanumerics and underscores, keep combining
marks attached to their base character, and preserve the separators between
words. `case_mix` starts uppercase, alternates across cased characters, and
preserves characters whose case mapping would expand them. `diacritic` adds
a combining acute accent to ASCII vowels. The fixed mappings are in
[operators.py](src/trustbreaker/operators.py).

## CLI

Install with `python -m pip install .`. The runtime uses Python's standard
library. `KeywordScanner` is a demo scanner that checks fixed case-insensitive
substrings. The optional `promptwarden` scanner uses the default Warden from
an importable PromptWarden installation.

```sh
trustbreaker mutate --text "team up!" --ops leet,space_out
python -m trustbreaker run --scanner keyword --corpus attacks/seed.jsonl
python -m trustbreaker run --scanner promptwarden --corpus attacks/seed.jsonl --out promptwarden-report.json
python -m trustbreaker run-traces --scanner agentsentinel --corpus traces.jsonl --out trace-report.json
```

The `run-traces` command (v0.2.0) does the same for agent traces: the corpus
is JSONL of bare trace objects or rows wrapping a `trace` object, the scanner
is `agentsentinel` or the toy `trace-keyword`, and the report carries the
same bypass accounting per trace operator.

The `mutate` command applies its comma-separated operators from left to right.
The `run` command reads UTF-8 JSONL with a string `text` and the label
`injection` on each line. It prints a summary table and writes `report.json` by
default. Use `--out` to set the path, `--budget` to set the maximum number of
unique variants scanned per text, and `--seed` to control tie-breaking. A
completed measurement exits successfully at any bypass rate. Usage errors
exit with status 2.

## Measured results

### AgentSentinel traces (v0.2.0)

New in v0.2.0: the same treatment for **agent traces** (`trustbreaker run-traces`).
Six trace operators — `noise_insert`, `tool_rename`, `arg_split`,
`reorder_independent`, `result_pad`, `path_obscure` — mutate step lists while
keeping them schema-valid. Against AgentSentinel 0.3.0 on its own eval corpus
(120 traces, budget 40, seed 13):

| AgentSentinel 0.3.0 | Originals flagged | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mutations of the 38 flagged traces | 38/120 | 1,465 | 540 | 36.86% | 63.14% |

Far more robust than PromptWarden — cross-step data-flow rules survive
cosmetic change — with one sharp edge: **`tool_rename` bypasses 79.22%** of
its applicable variants, because the scanner leans on exact tool names.
Details and reproduction: [benchmarks/README.md](benchmarks/README.md).

### PromptWarden corpus (v0.1.1)

The headline and the first chart are this run: PromptWarden 0.3.0 against its
own eval corpus, injection rows, budget 40, seed 13.

| PromptWarden 0.3.0 | Originals flagged | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mutations of the 74 caught attacks | 74/81 | 2,960 | 2,613 | 88.28% | 11.72% |

Per-operator rates are the bars above, from `leet` at 98.47% to `zero_width`
at 75.33%. Reproduction notes and the separate detection baseline are in the
[PromptWarden corpus baseline](benchmarks/README.md). Aggregates:
[promptwarden-corpus-summary.json](benchmarks/promptwarden-corpus-summary.json).

#### Fresh adaptive run against PromptWarden v0.4.0

Same protocol — 81 injection rows, budget 40, seed 13, UCB1 — with the
scanner bound to the sibling PromptWarden v0.4.0 checkout. This row is a new
adaptive measurement. It is separate from PromptWarden's fixed-set replay of
the v0.3.0 variants, which that project reports at 71.72% bypass.

| PromptWarden v0.4.0 (fresh adaptive) | Originals flagged | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mutations of the 75 caught attacks | 75/81 | 3,000 | 2,259 | 75.30% | 24.70% |

75.30% bypass is below the v0.3.0 fresh run (88.28%) and above PromptWarden's
fixed-set replay of that older variant mix (71.72%). The gap above 71.72% is
the bandit reallocating toward families that still bypass (`word_reverse`
92.32%, `char_reverse` 88.82%, `space_out` 88.21%). Details and the
per-operator table: [benchmarks/README.md](benchmarks/README.md). Aggregates:
[promptwarden-v040-fresh-summary.json](benchmarks/promptwarden-v040-fresh-summary.json).

#### Fresh adaptive run against PromptWarden v0.5.0

Same protocol — 81 injection rows, budget 40, seed 13, UCB1 — with the
scanner bound to the sibling PromptWarden v0.5.0 checkout. This row is a new
adaptive measurement. It is separate from PromptWarden's fixed-set replay of
the older variant mix, which that project reports as char_reverse 86.48% →
34.93% and word_reverse 91.97% → 33.24%.

| PromptWarden v0.5.0 (fresh adaptive) | Originals flagged | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mutations of the 78 caught attacks | 78/81 | 3,120 | 1,480 | 47.44% | 52.56% |

Fresh adaptive bypass is **88.28% → 75.30% → 47.44%** from v0.3.0 to v0.4.0
to v0.5.0 (robustness 11.72% → 24.70% → 52.56%). The bandit that concentrated
on `word_reverse` (92.32%) and `char_reverse` (88.82%) against v0.4.0 now
concentrates on `b64_wrap` (74.35%), `leet` (65.89%), and `space_out`
(65.64%). Details and the per-operator table:
[benchmarks/README.md](benchmarks/README.md). Aggregates:
[promptwarden-v050-fresh-summary.json](benchmarks/promptwarden-v050-fresh-summary.json).

#### Fresh adaptive run against PromptWarden v0.6.0

Same protocol — 81 injection rows, budget 40, seed 13, UCB1 — with the
scanner bound to the sibling PromptWarden v0.6.0 checkout. This row is a new
adaptive measurement. It is separate from PromptWarden's fixed composition
replay (depth-2 bypass 30.80% → 11.36%, nested base64 100% → 7.69%) and from
its replay of the frozen 2,960-variant set (42.91% → 19.22%).

| PromptWarden v0.6.0 (fresh adaptive) | Originals flagged | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mutations of the 78 caught attacks | 78/81 | 3,120 | 676 | 21.67% | 78.33% |

Fresh adaptive bypass is **88.28% → 75.30% → 47.44% → 21.67%** from v0.3.0
to v0.4.0 to v0.5.0 to v0.6.0 (robustness 11.72% → 24.70% → 52.56% →
78.33%). The bandit that concentrated on `b64_wrap` (74.35%), `leet`
(65.89%), and `space_out` (65.64%) against v0.5.0 still applies `leet` most
often (835 applicable, 36.77%) and `b64_wrap` next (809, 39.18%), with
`case_mix` third (768, 28.12%). Details and the per-operator table:
[benchmarks/README.md](benchmarks/README.md). Aggregates:
[promptwarden-v060-fresh-summary.json](benchmarks/promptwarden-v060-fresh-summary.json).

### Seed corpus (v0.1.0)

Seed corpus `attacks/seed.jsonl` (12 synthetic attacks written for this
project — **not** any scanner's own benchmark corpus), budget 40 variants per
text, seed 13. Reproduced deterministically: two identical runs produce
identical reports. The second chart reads the robustness column.
[seed-summary.json](benchmarks/seed-summary.json) mirrors this table.

| Scanner | Originals flagged | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: | ---: |
| KeywordScanner (naive substring) | 12/12 | 480 | 472 | 98.33% | 1.67% |
| PromptWarden 0.3.0 | 6/12 | 240 | 208 | 86.67% | 13.33% |

Read the PromptWarden row carefully: half the seed attacks were not flagged
even unmutated, so they contribute no variants — the 86.67% is the bypass rate
over mutations of the six attacks it did catch.

Per-family bypass against PromptWarden on this seed run (not the corpus chart above):

| Operator | Bypass rate |
| --- | ---: |
| `leet` | 100% |
| `char_reverse` | 100% |
| `diacritic` | 97.9% |
| `space_out` | 96.2% |
| `word_reverse` | 95.9% |
| `punct_split` | 94.3% |
| `b64_wrap` | 83.7% |
| `case_mix` | 81.8% |
| `homoglyph` | 78.2% |
| `synonym` | 76.8% |
| `zero_width` | 67.4% |

Transforms are exactly the blind spot PromptWarden's own benchmark reported;
TrustBreaker quantifies it.

Regenerate both charts with `python3 docs/assets/make_charts.py`.

## Interpreting reports

- A bypass requires a flagged original and an unflagged variant. Variants of
  unflagged originals are marked `not_applicable` and excluded from all
  bypass-rate denominators.
- The robustness score is one minus the overall bypass rate. Rates and the
  robustness score use `null` when their denominator is empty.
- A composed variant contributes once to each operator it uses and once to its
  exact pipeline. The overall rate counts each applicable variant once.
- Exact mutated text and scanner verdicts are recorded with every variant so
  measured bypasses can be reproduced.
- TrustBreaker measures scanners. Scanner training, tuning, and editing are
  outside its workflow. The synthetic seed corpus is measurement data and
  stays out of scanner training.
