# PromptWarden corpus baseline

The run used PromptWarden's default scanner and its 181-row corpus at
`../promptwarden/evals/corpus.jsonl`.

| PromptWarden | Injection rows | Flagged | Missed | Detection rate |
| --- | ---: | ---: | ---: | ---: |
| 0.3.0 | 81 | 74 | 7 | 91.36% |

This measures detection of original injection examples on PromptWarden's home
distribution. TrustBreaker uses the corpus solely for measurement. PromptWarden
used a portion of these rows for model fitting, so the result describes
detection on the full injection subset.

With TrustBreaker and PromptWarden installed, run the baseline from the
TrustBreaker root.

```sh
python benchmarks/run_promptwarden_corpus.py
```

The script searches the installed PromptWarden package and the sibling checkout,
prints the corpus path used, and writes the [baseline JSON](promptwarden-corpus-baseline.json).

## Mutation measurement (TrustBreaker v0.1.1)

The 74 flagged originals were then mutated by TrustBreaker (budget 40 variants
per text, seed 13, UCB1 allocation over operator pipelines):

| PromptWarden 0.3.0 | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: |
| Mutations of the 74 caught attacks | 2,960 | 2,613 | **88.28%** | **11.72%** |

Per-operator bypass rate: `leet` 98.47%, `diacritic` 97.77%, `space_out` 95.56%,
`punct_split` 95.33%, `word_reverse` 93.66%, `char_reverse` 92.68%, `b64_wrap`
89.93%, `synonym` 82.00%, `case_mix` 81.73%, `homoglyph` 79.46%, `zero_width`
75.33% (least effective — PromptWarden has normalized zero-width characters
since v0.2.0).

Aggregates live in
[promptwarden-corpus-summary.json](promptwarden-corpus-summary.json). The full
per-variant report is deliberately **not** published: it records thousands of
working bypass payloads. Reproduce it locally with the TrustBreaker CLI
against the PromptWarden corpus; two runs with the same seed produce identical
summaries. Originals the scanner does not flag are excluded from the bypass
rate by design — detection (above) and evasion (here) are separate numbers.

## Fresh adaptive run (PromptWarden v0.4.0)

`run_promptwarden_v040_fresh.py` repeats that protocol on the same 81 injection
rows (budget 40, seed 13, UCB1 over operator pipelines) with the scanner bound
to the sibling checkout `../promptwarden` at v0.4.0. The script inserts that
checkout's `src` ahead of site-packages, so an older installed PromptWarden
cannot satisfy the import. v0.4.0 flags 75 of the 81 originals.

| PromptWarden 0.4.0 | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: |
| Fresh adaptive mutations of the 75 caught attacks | 3,000 | 2,259 | **75.30%** | **24.70%** |

Per-operator rates (a variant counts toward every operator in its pipeline, so
families overlap):

| Operator | Applicable | Bypasses | Bypass rate |
| --- | ---: | ---: | ---: |
| `word_reverse` | 768 | 709 | 92.32% |
| `char_reverse` | 760 | 675 | 88.82% |
| `space_out` | 780 | 688 | 88.21% |
| `b64_wrap` | 742 | 640 | 86.25% |
| `leet` | 738 | 625 | 84.69% |
| `diacritic` | 708 | 490 | 69.21% |
| `punct_split` | 685 | 472 | 68.91% |
| `synonym` | 690 | 472 | 68.41% |
| `case_mix` | 719 | 489 | 68.01% |
| `homoglyph` | 699 | 449 | 64.23% |
| `zero_width` | 681 | 409 | 60.06% |

The v0.3.0 fresh run bypassed **88.28%** (robustness 11.72%). PromptWarden's
README reports a fixed-set replay of those same 2,960 variants against v0.4.0
at **71.72%** bypass (robustness 28.28%). The fresh adaptive figure is
**75.30%** (robustness 24.70%). A fresh number can differ from a fixed-set
replay because UCB1 reallocates toward surviving families. The 71.72% rescores
the variants chosen while v0.3.0 was the target, when `leet`, `diacritic`,
`space_out`, and `punct_split` cleared 95–98% of their applicable variants.
v0.4.0 folds diacritics, de-leets word-shaped tokens, and rejoins short spaced
and punctuation-split fragments, and about 16 percentage points of that frozen
mix are now caught. The fresh run starts the bandit again, from the same seed,
against v0.4.0, and later pulls shift toward the families that still clear
most often: `word_reverse` 92.32%, `char_reverse` 88.82%, and `space_out`
88.21%, with `b64_wrap` 86.25% and `leet` 84.69% still high. That
reallocation is why the adaptive bypass rate is above the fixed-set replay,
and the normalization is why both v0.4.0 figures are below the v0.3.0 fresh
run. The denominator moves with the scanner as well: 75 flagged originals and
3,000 applicable variants, against 74 and 2,960 before.

Aggregates:
[promptwarden-v040-fresh-summary.json](promptwarden-v040-fresh-summary.json).
Per-variant payloads are never written. Reproduce from the TrustBreaker root
with the sibling PromptWarden v0.4.0 checkout present:

```sh
python benchmarks/run_promptwarden_v040_fresh.py
```

Two runs with this seed write byte-identical aggregates.

## Fresh adaptive run (PromptWarden v0.5.0)

`run_promptwarden_v050_fresh.py` repeats that protocol on the same 81 injection
rows (budget 40, seed 13, UCB1 over operator pipelines) with the scanner bound
to the sibling checkout `../promptwarden` at v0.5.0. The script inserts that
checkout's `src` ahead of site-packages, so an older installed PromptWarden
cannot satisfy the import. v0.5.0 flags 78 of the 81 originals.

| PromptWarden 0.5.0 | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: |
| Fresh adaptive mutations of the 78 caught attacks | 3,120 | 1,480 | **47.44%** | **52.56%** |

Per-operator rates (a variant counts toward every operator in its pipeline, so
families overlap):

| Operator | Applicable | Bypasses | Bypass rate |
| --- | ---: | ---: | ---: |
| `b64_wrap` | 846 | 629 | 74.35% |
| `leet` | 812 | 535 | 65.89% |
| `space_out` | 815 | 535 | 65.64% |
| `diacritic` | 745 | 335 | 44.97% |
| `punct_split` | 743 | 328 | 44.15% |
| `case_mix` | 731 | 301 | 41.18% |
| `synonym` | 721 | 286 | 39.67% |
| `char_reverse` | 734 | 291 | 39.65% |
| `word_reverse` | 736 | 291 | 39.54% |
| `homoglyph` | 727 | 262 | 36.04% |
| `zero_width` | 718 | 248 | 34.54% |

Fresh adaptive bypass falls from **88.28%** on v0.3.0 to **75.30%** on v0.4.0 to
**47.44%** on v0.5.0 (robustness 11.72% → 24.70% → 52.56%). v0.5.0 scores
character-reversed and word-reversed views when they carry a decisive
instruction pattern, with the same context masking as the direct view. On the
v0.4.0 fresh run the bandit had concentrated on those families (`word_reverse`
92.32%, `char_reverse` 88.82%), alongside `space_out` 88.21%, `b64_wrap`
86.25%, and `leet` 84.69%. Here `word_reverse` is 39.54% and `char_reverse` is
39.65%. PromptWarden's fixed-set replay of the v0.3.0 variant mix shows the
same drop at a lower level (char_reverse 86.48% → 34.93%, word_reverse 91.97%
→ 33.24%). The fresh rates sit a few points above that floor in the room the
changelog still lists as open: reversal composed with spacing across word
boundaries, or with synonym substitution, which the reversal pass leaves
uninverted. The families that still clear most often, and that this run
applies most often, are `b64_wrap` 74.35% (846 applicable), `leet` 65.89%
(812), and `space_out` 65.64% (815). Every other operator is under 45%, with
`zero_width` at 34.54%. The denominator moves with detection: 78 flagged
originals and 3,120 applicable variants, against 75 and 3,000 on the v0.4.0
fresh run.

Aggregates:
[promptwarden-v050-fresh-summary.json](promptwarden-v050-fresh-summary.json).
Per-variant payloads are never written. Reproduce from the TrustBreaker root
with the sibling PromptWarden v0.5.0 checkout present:

```sh
python benchmarks/run_promptwarden_v050_fresh.py
```

Two runs with this seed write byte-identical aggregates.

## Fresh adaptive run (PromptWarden v0.6.0)

`run_promptwarden_v060_fresh.py` repeats that protocol on the same 81 injection
rows (budget 40, seed 13, UCB1 over operator pipelines) with the scanner bound
to the sibling checkout `../promptwarden` at v0.6.0. The script inserts that
checkout's `src` ahead of site-packages, so an older installed PromptWarden
cannot satisfy the import. v0.6.0 flags 78 of the 81 originals, the same count
as v0.5.0. The bundled model was not refit. PromptWarden reports the same
corpus operating point as v0.5.0 (F1 0.9035, FPR 0.0667).

| PromptWarden 0.6.0 | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: |
| Fresh adaptive mutations of the 78 caught attacks | 3,120 | 676 | **21.67%** | **78.33%** |

Per-operator rates (a variant counts toward every operator in its pipeline, so
families overlap):

| Operator | Applicable | Bypasses | Bypass rate |
| --- | ---: | ---: | ---: |
| `b64_wrap` | 809 | 317 | 39.18% |
| `leet` | 835 | 307 | 36.77% |
| `case_mix` | 768 | 216 | 28.12% |
| `word_reverse` | 759 | 174 | 22.92% |
| `space_out` | 771 | 174 | 22.57% |
| `punct_split` | 752 | 161 | 21.41% |
| `char_reverse` | 740 | 136 | 18.38% |
| `synonym` | 744 | 122 | 16.40% |
| `diacritic` | 724 | 101 | 13.95% |
| `zero_width` | 715 | 99 | 13.85% |
| `homoglyph` | 702 | 84 | 11.97% |

Fresh adaptive bypass falls from **88.28%** on v0.3.0 to **75.30%** on v0.4.0 to
**47.44%** on v0.5.0 to **21.67%** on v0.6.0 (robustness 11.72% → 24.70% →
52.56% → 78.33%). This step holds the denominator fixed: 78 flagged originals
and 3,120 applicable variants, the same as the v0.5.0 fresh run. v0.6.0 adds
composed views — a de-spaced reading of reversed text, a reversed reading of
de-leeted text, and a second standard-base64 decode — still decisive-only and
still masked. On the v0.5.0 fresh run the bandit was living on `b64_wrap`
74.35% (846 applicable), `leet` 65.89% (812), and `space_out` 65.64% (815).
Those rates are now 39.18% (809), 36.77% (835), and 22.57% (771). The
reallocation is mild. There are 1,463 pipelines and the budget pulls almost
every arm two or three times (1,135 twice, 322 three times), so applicable
counts stay inside 702–835. Within that band the run applies `leet` most often
(835) and `b64_wrap` next (809). `case_mix` is the count that rose (731 → 768)
and the new third-highest rate, 28.12%. That ordering is the remaining
surface. Every other operator is under 23%, with `homoglyph` at 11.97%. The
bypasses themselves are spread out: depth-3 arms are 1,331 of 1,463, this run
puts 2,852 of 3,120 applicable variants there, and 661 of the 676 bypasses
sit on depth 3, across 447 pipelines. Depth 1 is 1/23 and depth 2 is 14/245;
6 of those 14 are `b64_wrap+leet` and `b64_wrap+case_mix`. Every applicable
variant in this run whose pipeline applies `leet` or `case_mix` after
`b64_wrap` bypassed (186/186). Those two transforms knock the payload off the
standard base64 alphabet, and the second decode has nothing intact to read.
Pipelines that include none of `b64_wrap`, `leet`, and `case_mix` bypass 9.87%
(116/1,175) and supply 17.16% of the bypasses. Reversal is still inside 42.46%
of bypasses, at a 20.98% marginal rate. Synonym substitution, which has no
inverse, is 16.40% here. PromptWarden's fixed-set figures are a separate
measurement: depth-2 compositions 30.80% → 11.36%, nested base64 100% → 7.69%
(6/78, injections no decisive rule names), and the frozen 2,960-variant replay
42.91% → 19.22%. This fresh 21.67% is a new adaptive draw. It lands next to
that frozen replay, and above the fixed depth-2 figure, because the bandit
keeps sampling the depth-3 catalog and the base64-then-leet /
base64-then-case-mix shape the composed views leave open.

Aggregates:
[promptwarden-v060-fresh-summary.json](promptwarden-v060-fresh-summary.json).
Per-variant payloads are never written. Reproduce from the TrustBreaker root
with the sibling PromptWarden v0.6.0 checkout present:

```sh
python benchmarks/run_promptwarden_v060_fresh.py
```

Two runs with this seed write byte-identical aggregates.

# AgentSentinel corpus baseline

AgentSentinel 0.3.0's default scanner scanned each of the 120 original traces
in `../agentsentinel/evals/corpus.jsonl` once.

| Corpus label | Originals | Flagged | Flagged rate |
| --- | ---: | ---: | ---: |
| Malicious | 40 | 33 | 82.50% |
| Benign | 80 | 5 | 6.25% |
| All | 120 | 38 | 31.67% |

The flagged malicious subset contains 33 originals. The benchmark uses the eval
corpus solely for measurement. It passes each trace to the scanner as recorded
and stores only the aggregate counts in
[agentsentinel-corpus-summary.json](agentsentinel-corpus-summary.json).

To reproduce from the TrustBreaker root with the sibling AgentSentinel checkout:

```sh
PYTHONPATH=src:../agentsentinel/src python benchmarks/run_agentsentinel_corpus.py
```

## AgentSentinel trace mutation (v0.2.0)

`run_agentsentinel_mutation.py` feeds all 120 corpus traces to `TraceBreaker`
with the AgentSentinel scanner (budget 40 variants per trace, seed 13, UCB1
over trace-operator pipelines). Only traces the scanner flags produce
applicable variants: 38 originals (33 malicious, 5 benign).

| Scope | Applicable | Bypasses | Bypass rate |
|---|---:|---:|---:|
| All applicable variants | 1,465 | 540 | 36.86% |

Robustness score: **63.14%** — markedly stronger than PromptWarden's 11.72% on
its own corpus, because AgentSentinel's rules track cross-step data flow,
which survives cosmetic change. Per-operator rates (a variant counts toward
every operator in its pipeline, so families overlap):

| Operator | Applicable | Bypasses | Bypass rate |
|---|---:|---:|---:|
| tool_rename | 645 | 511 | 79.22% |
| noise_insert | 837 | 295 | 35.24% |
| reorder_independent | 550 | 173 | 31.45% |
| result_pad | 649 | 190 | 29.28% |
| arg_split | 422 | 119 | 28.20% |
| path_obscure | 450 | 113 | 25.11% |

The one sharp edge is `tool_rename`: AgentSentinel leans on exact tool names,
so calling `http_post` a `webhook_call` defeats most of its applicable
variants. Aggregates live in
[agentsentinel-mutation-summary.json](agentsentinel-mutation-summary.json);
per-variant mutated traces are never written to disk.

To reproduce from the TrustBreaker root with the sibling AgentSentinel
checkout installed:

```sh
python benchmarks/run_agentsentinel_mutation.py
```

### Post-fix re-measurement (AgentSentinel v0.4.0)

AgentSentinel v0.4.0 answered this benchmark with tool-name canonicalization.
Re-running the identical protocol against the shipped v0.4.0 build:
**bypass 36.86% → 2.94%, robustness 63.14% → 97.06%** (43 of 1,465 variants),
with `tool_rename` down from 79.22% to 2.24%. Detection on the original
corpus is unchanged (F1 0.8462, FPR 0.0625). Aggregates:
[agentsentinel-mutation-summary-v040.json](agentsentinel-mutation-summary-v040.json).
