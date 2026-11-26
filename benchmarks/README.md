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

## Fresh adaptive run (PromptWarden v0.7.0)

`run_promptwarden_v070_fresh.py` repeats that protocol on the same 81 injection
rows (budget 40, seed 13, UCB1 over operator pipelines) with the scanner bound
to the sibling checkout `../promptwarden` at v0.7.0. The script inserts that
checkout's `src` ahead of site-packages, so an older installed PromptWarden
cannot satisfy the import. v0.7.0 flags 78 of the 81 originals, the same count
as v0.6.0 and v0.5.0. The bundled model was not refit. PromptWarden reports the
same corpus operating point as v0.6.0 (F1 0.9035, FPR 0.0667).

| PromptWarden 0.7.0 | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: |
| Fresh adaptive mutations of the 78 caught attacks | 3,120 | 610 | **19.55%** | **80.45%** |

Per-operator rates (a variant counts toward every operator in its pipeline, so
families overlap):

| Operator | Applicable | Bypasses | Bypass rate |
| --- | ---: | ---: | ---: |
| `b64_wrap` | 794 | 278 | 35.01% |
| `leet` | 831 | 287 | 34.54% |
| `case_mix` | 763 | 205 | 26.87% |
| `space_out` | 758 | 151 | 19.92% |
| `punct_split` | 757 | 145 | 19.15% |
| `word_reverse` | 746 | 141 | 18.90% |
| `char_reverse` | 754 | 127 | 16.84% |
| `synonym` | 749 | 119 | 15.89% |
| `zero_width` | 723 | 93 | 12.86% |
| `diacritic` | 731 | 89 | 12.18% |
| `homoglyph` | 705 | 71 | 10.07% |

Fresh adaptive bypass falls from **88.28%** on v0.3.0 to **75.30%** on v0.4.0 to
**47.44%** on v0.5.0 to **21.67%** on v0.6.0 to **19.55%** on v0.7.0 (robustness
11.72% → 24.70% → 52.56% → 78.33% → 80.45%). The denominator stays put: 78
flagged originals and 3,120 applicable variants, the same as the v0.5.0 and
v0.6.0 fresh runs, and the drop is 66 bypasses. v0.7.0 decodes URL-safe and
triple-layer base64, a second percent or hex unescape, and word-order system
fences. This catalog can express only the standard-base64 part of that list.
The exact double-wrap and triple-wrap arms this seed pulled were caught (0/2
and 0/2), and stacked base64 with no later `leet` or `case_mix` bypasses 4/56.
The pull histogram is almost the v0.6.0 histogram. There are 1,463 pipelines
and 3,240 pulls: 1,137 arms twice, 321 three times, 3 once, and 2 never, next
to 1,135 twice and 322 three times on v0.6.0. Applicable counts stay inside
705–831. The run still applies `leet` most often (831), `b64_wrap` next (794),
and `case_mix` third (763), and those three still have the highest rates
(34.54%, 35.01%, 26.87%). The reliable hole inside that band matches one of
the three classes PromptWarden's changelog still names. Every catalog pipeline
that applies `leet` or `case_mix` after `b64_wrap` bypassed, 186/186, across
all 62 such pipelines, each pulled three times. Those 62 are 62 of the 77 arms
that bypassed on every pull, and they account for 186 of the 610 bypasses:
leet or case-mixing inside the base64 blob destroys bits the decoder does not
guess. The other two named classes stay open at ordinary rates, and the third
pulls do not gather there. Synonym substitution has no inverse and bypasses at
15.89% (119/749), under the run rate; its applicable count moved from 744 to
749. Depth-2 `b64_wrap` with `synonym`, either order, was caught (0/2).
Synonym shows up on a never-failing arm only beside base64-then-leet or
base64-then-case-mix, and bypasses that carry synonym without the other two
markers are 83/610. Ambiguous hyphen splits are the remaining mismatch.
`punct_split` bypasses at 19.15% (145/757), in line with the run, and the
depth-2 arm that hyphen-splits a standard base64 blob was caught (0/2). The
changelog's open case is a URL-safe hyphen that cannot be told from an inserted
separator. `b64_wrap` emits standard base64, so this run never builds that
ambiguity and the applicable count only moves from 752 to 757. Bypasses that
carry a hyphen split without the other two markers are 109/610. Another
214/610 bypasses carry none of the three markers. They sit in the depth-3 tail —
591 of 610 bypasses are depth 3 — where two or three pulls can still clear
without a second family
at 186/186. PromptWarden's fixed-set figures are a separate measurement:
ordered pairs 11.36% → 10.10%, the historical 2,960-variant replay 19.22% →
17.70%, and base64 followed by leet or by case mixing still 78/78. This fresh
19.55% is a new adaptive draw. It lands beside that frozen replay because the
bandit keeps sampling depth 3 and the base64-then-leet / base64-then-case-mix
shape the decoder leaves open.

Aggregates:
[promptwarden-v070-fresh-summary.json](promptwarden-v070-fresh-summary.json).
Per-variant payloads are never written. Reproduce from the TrustBreaker root
with the sibling PromptWarden v0.7.0 checkout present:

```sh
python benchmarks/run_promptwarden_v070_fresh.py
```

Two runs with this seed write byte-identical aggregates.

## Fresh adaptive run (PromptWarden v0.7.1)

`run_promptwarden_v071_fresh.py` repeats that protocol on the same 81 injection rows (budget 40, seed 13, UCB1 over operator pipelines) with the scanner bound to the sibling checkout `../promptwarden` at v0.7.1. The script inserts that checkout's `src` ahead of site-packages, so an older installed PromptWarden cannot satisfy the import. v0.7.1 flags 78 of the 81 originals, the same count as v0.7.0. The bundled model was not refit. PromptWarden reports the same corpus operating point as v0.7.0 (F1 0.9035, FPR 0.0667).

| PromptWarden 0.7.1 | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: |
| Fresh adaptive mutations of the 78 caught attacks | 3,120 | 727 | **23.30%** | **76.70%** |

Per-operator rates (a variant counts toward every operator in its pipeline, so families overlap):

| Operator | Applicable | Bypasses | Bypass rate |
| --- | ---: | ---: | ---: |
| `leet` | 830 | 312 | 37.59% |
| `b64_wrap` | 801 | 297 | 37.08% |
| `word_reverse` | 780 | 237 | 30.38% |
| `case_mix` | 764 | 220 | 28.80% |
| `zero_width` | 751 | 184 | 24.50% |
| `space_out` | 748 | 159 | 21.26% |
| `punct_split` | 743 | 157 | 21.13% |
| `char_reverse` | 746 | 151 | 20.24% |
| `synonym` | 741 | 127 | 17.14% |
| `diacritic` | 726 | 115 | 15.84% |
| `homoglyph` | 699 | 90 | 12.88% |

Fresh adaptive bypass is **88.28% → 75.30% → 47.44% → 21.67% → 19.55% → 23.30%** from v0.3.0 to v0.4.0 to v0.5.0 to v0.6.0 to v0.7.0 to v0.7.1 (robustness 11.72% → 24.70% → 52.56% → 78.33% → 80.45% → 76.70%). The denominator stays put: 78 flagged originals and 3,120 applicable variants, the same as the v0.5.0, v0.6.0, and v0.7.0 fresh runs. Bypasses move from 610 to 727.

The bandit still applies `leet` most often (830 applicable, 37.59%) and `b64_wrap` next (801, 37.08%). `word_reverse` is now third (780, 30.38%) and `case_mix` fourth (764, 28.80%). On the v0.7.0 fresh run the third family was `case_mix` (763, 26.87%) and `word_reverse` was 746 applicable at 18.90%. `zero_width` rises with `word_reverse`, from 723 applicable and 12.86% to 751 and 24.50%. The pull histogram barely moves. There are 1,463 pipelines and 3,240 pulls: 1,135 arms twice, 322 three times, 4 once, and 2 never, next to 1,137 twice, 321 three times, 3 once, and 2 never on v0.7.0. Applicable counts stay inside 699–830. Always-clear arms go from 77 to 103 (309 variants, each of those arms pulled three times). The 62 pipelines that apply `leet` or `case_mix` after `b64_wrap` are still all clear, 186/186. Of the other 41 always-clear pipelines, 24 contain both `word_reverse` and `zero_width`.

v0.7.1's Unicode normalization change is what moves this surface. The release applies NFKC and strips format characters and non-whitespace controls before every instruction view, and the reversal pass now reverses those canonical bases. This catalog does not emit the characters that fix was measured on. No operator inserts a bidi mark, word joiner, soft hyphen, NUL, other C0 or C1 control, or a fullwidth letter. `zero_width` still inserts only U+200B, which v0.7.0 already deleted. Two injection rows contain compatibility characters; 55 applicable variants in this run still contain one, and none of those 55 bypass. Rescanning the variants chosen here with v0.7.0 flags every one of the 2,393 that v0.7.1 flags, and also flags 119 that v0.7.1 leaves clear. A separate v0.7.0 adaptive run under this harness reproduces the published 610 and the published per-operator counts, so the schedules are not the same set: v0.7.0 would clear 608 of the variants chosen this time. The published totals differ by 117.

Those 119 misses concentrate on one order. `zero_width` splits each word into letters. `word_reverse` then treats U+200B as a word boundary, reverses the letters, and leaves the marks in the original slots. v0.7.0 built a reversal view from that raw string, so reversing the letters again restored the instruction before the marks were deleted. v0.7.1 deletes the marks first. The shuffled letters glue into the original word slots, and reversing those glued words does not restore the instruction. On the public sentence "Ignore all previous instructions", `zero_width` then `word_reverse` scores 0.85 on v0.7.0 and 0.0712 on v0.7.1. The direct normalized text is the same on both versions, and recovered reversal views fall from 1 to 0. `word_reverse` then `zero_width` still flags on both versions. 69 of the 119 apply `zero_width` before `word_reverse`, and 55 of those 69 keep the same direct normalization and differ in the reversal views. The other 50 are mixed: 25 carry `word_reverse` without `zero_width`, 19 carry `zero_width` without `word_reverse`, 3 apply `word_reverse` first, and 3 contain neither. 38 of the 119 also change the direct normalized text. 11 keep the same direct, reversal, and composed view text, so those flags move on a reading outside the three views hashed here. The decoder's carrier repair changed in the same release. Depth 3 holds 711 of the 727 bypasses. Depth 1 is 1/23 and depth 2 is 15/243. The base64-then-leet and base64-then-case-mix shape still accounts for 186 bypasses. The zero-width-then-word-reverse order accounts for 69 of the 119 new misses and is what pushes the fresh rate above the v0.7.0 result.

Aggregates:
[promptwarden-v071-fresh-summary.json](promptwarden-v071-fresh-summary.json).
Per-variant payloads are never written. Reproduce from the TrustBreaker root
with the sibling PromptWarden v0.7.1 checkout present:

```sh
python benchmarks/run_promptwarden_v071_fresh.py
```

Two runs with this seed write byte-identical aggregates.

## Fresh adaptive run (PromptWarden v0.8.0)

`run_promptwarden_v080_fresh.py` repeats that protocol on the same 81 injection rows (budget 40, seed 13, UCB1 over operator pipelines) with the scanner bound to the sibling checkout `../promptwarden` at v0.8.0. The script inserts that checkout's `src` ahead of site-packages, so an older installed PromptWarden cannot satisfy the import. v0.8.0 flags 78 of the 81 originals, the same count as v0.7.1. The bundled model was not refit. PromptWarden reports the same corpus operating point as v0.7.1 (F1 0.9035, FPR 0.0667).

| PromptWarden 0.8.0 | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: |
| Fresh adaptive mutations of the 78 caught attacks | 3,120 | 719 | **23.04%** | **76.96%** |

Per-operator rates (a variant counts toward every operator in its pipeline, so families overlap):

| Operator | Applicable | Bypasses | Bypass rate |
| --- | ---: | ---: | ---: |
| `leet` | 825 | 305 | 36.97% |
| `b64_wrap` | 791 | 286 | 36.16% |
| `word_reverse` | 782 | 237 | 30.31% |
| `case_mix` | 761 | 216 | 28.38% |
| `zero_width` | 751 | 182 | 24.23% |
| `space_out` | 751 | 159 | 21.17% |
| `punct_split` | 746 | 157 | 21.05% |
| `char_reverse` | 747 | 151 | 20.21% |
| `synonym` | 741 | 128 | 17.27% |
| `diacritic` | 728 | 117 | 16.07% |
| `homoglyph` | 701 | 89 | 12.70% |

Fresh adaptive bypass is **88.28% → 75.30% → 47.44% → 21.67% → 19.55% → 23.30% → 23.04%** from v0.3.0 to v0.4.0 to v0.5.0 to v0.6.0 to v0.7.0 to v0.7.1 to v0.8.0 (robustness 11.72% → 24.70% → 52.56% → 78.33% → 80.45% → 76.70% → 76.96%). The denominator stays put: 78 flagged originals and 3,120 applicable variants, the same as the v0.5.0, v0.6.0, v0.7.0, and v0.7.1 fresh runs. Bypasses move from 727 to 719.

The bandit still applies `leet` most often (825 applicable, 36.97%) and `b64_wrap` next (791, 36.16%). `word_reverse` is third (782, 30.31%) and `case_mix` fourth (761, 28.38%). On the v0.7.1 fresh run those four were `leet` 830 at 37.59%, `b64_wrap` 801 at 37.08%, `word_reverse` 780 at 30.38%, and `case_mix` 764 at 28.80%. The pull histogram barely moves. There are 1,463 pipelines and 3,240 pulls: 1,139 arms twice, 320 three times, 2 once, and 2 never, next to 1,135 twice, 322 three times, 4 once, and 2 never on v0.7.1. Applicable counts stay inside 701–825. Of the 320 arms pulled three times, 150 contain `leet`, 110 contain `word_reverse`, and 108 contain `b64_wrap`. Always-clear arms stay at 103 (309 variants, each of those arms pulled three times). The 62 pipelines that apply `leet` or `case_mix` after `b64_wrap` are still all clear, 186/186. Of the other 41 always-clear pipelines, 24 contain both `word_reverse` and `zero_width`.

Decoded-deleet changes a thin inside-encoding slice and leaves the carrier slice alone. Rescanning the variants chosen here with v0.7.1 flags 2,392 of them. v0.8.0 flags those 2,392 and 9 more. v0.7.1 leaves 728 clear, and v0.8.0 leaves 719 clear. No variant that v0.8.0 misses is flagged by v0.7.1. The 9 are all depth 3, one variant each. Seven leet the text and only then wrap it, with no later `leet` or `case_mix` on the carrier: `leet+leet+b64_wrap`, `leet+case_mix+b64_wrap`, `case_mix+leet+b64_wrap`, `space_out+leet+b64_wrap`, `synonym+leet+b64_wrap`, `leet+b64_wrap+homoglyph`, and `leet+b64_wrap+zero_width`. The other two are `case_mix+b64_wrap+word_reverse` and `case_mix+b64_wrap+zero_width`. That is leet or case-mix inside an intact wrap, which is the class the decoded views read. The opposite order is the class v0.8.0 still names as open, and this run agrees. All 186 variants that apply `leet` or `case_mix` after `b64_wrap` bypass on both versions. Depth-2 `b64_wrap+leet` and `b64_wrap+case_mix` are 3/3. Depth-2 `leet+b64_wrap` and `case_mix+b64_wrap` are 0/2 on both versions, so a single leet or case-mix inside one wrap was already flagged on the pulls this seed took. Across the inside-encoding variants the bandit did pull, leet before the last wrap with the carrier left intact is 59 applicable: v0.8.0 misses 10 and v0.7.1 misses 17. Case-mix inside an intact carrier is 58 applicable: 11 misses against 15. Those slices overlap. The 7 leet catches include the 2 pipelines that also case-mix before the wrap, and the case-mix drop of 4 is those 2 plus the 2 case-mix-only pipelines. Pipelines that contain `leet` and no `b64_wrap` are 199/670 on both versions. The loose deleet runs on text the decoder already yielded. Depth 1 stays 1/23 and depth 2 stays 15/243. Depth 3 holds 703 of the 719 bypasses.

Those 9 are the adaptive sample, not the size of the class. Applied to every flagged original, outside this budget, the same pipelines flip more rows. `case_mix+leet+b64_wrap`, `leet+case_mix+b64_wrap`, and `leet+b64_wrap+zero_width` each flip 16. `leet+leet+b64_wrap` and `leet+b64_wrap+homoglyph` flip 15. `synonym+leet+b64_wrap` flips 14. `space_out+leet+b64_wrap` flips 2. Each case-mix-then-wrap pipeline flips 1. The bandit holds one flip from each pipeline. Its third pulls still gather on the carrier-damage arms, which pay on every pull.

Dehyphenation does not show up on this catalog. `punct_split` bypasses 157 variants on both versions (746 applicable here, 21.05%, from 743 applicable and 21.13% on v0.7.1). All 746 get the same flag from v0.7.1. None of the 9 newly flagged pipelines is `punct_split`. Every flipped variant of those nine pipelines contains no hyphen, so the outer dehyphen pass has nothing to join. `punct_split` puts a hyphen between every character. The shared normalizer has rejoined a run of one- and two-letter pieces, at least three pieces long, since v0.4.0. The dehyphenated view joins a longer fragment, such as `ig-nore`, and a hyphen at a line break. This catalog emits neither.

`word_reverse` did the same work as on v0.7.1. It bypasses 237 variants here and 237 on that run. Applicable goes from 780 to 782, so the rate goes from 30.38% to 30.31%. The one paired disagreement that contains `word_reverse` is `case_mix+b64_wrap+word_reverse`, one of the nine inside-encoding catches, and that original has no hyphen. The order that raised this family on v0.7.1 is still where it clears. `zero_width` before `word_reverse` bypasses 80/91 (87.91%), and v0.7.1 flags every one of those 91 the same way. `word_reverse` before `zero_width` bypasses 14/66 (21.21%). `word_reverse` with no `zero_width` bypasses 149/631 (23.61%).

Aggregates:
[promptwarden-v080-fresh-summary.json](promptwarden-v080-fresh-summary.json).
Per-variant payloads are never written. Reproduce from the TrustBreaker root
with the sibling PromptWarden v0.8.0 checkout present:

```sh
python benchmarks/run_promptwarden_v080_fresh.py
```

Two runs with this seed write byte-identical aggregates.

## Fresh adaptive run (PromptWarden v0.9.0)

`run_promptwarden_v090_fresh.py` repeats that protocol on the same 81 injection rows (budget 40, seed 13, UCB1 over operator pipelines) with the scanner bound to the sibling checkout `../promptwarden` at v0.9.0. v0.9.0 flags 78 of the 81 originals, the same count as v0.8.1. The bundled model was not refit. PromptWarden reports the same corpus operating point (F1 0.9035, FPR 0.0667). Run twice; aggregates byte-identical.

| PromptWarden 0.9.0 | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: |
| Fresh adaptive mutations of the 78 caught attacks | 3,120 | 570 | **18.27%** | **81.73%** |

Per-operator rates (a variant counts toward every operator in its pipeline, so families overlap):

| Operator | Applicable | Bypasses | Bypass rate |
| --- | ---: | ---: | ---: | ---:|
| `b64_wrap` | 789 | 261 | 33.08% |
| `leet` | 814 | 261 | 32.06% |
| `case_mix` | 768 | 191 | 24.87% |
| `punct_split` | 770 | 144 | 18.70% |
| `space_out` | 755 | 131 | 17.35% |
| `word_reverse` | 731 | 112 | 15.32% |
| `synonym` | 746 | 111 | 14.88% |
| `char_reverse` | 749 | 109 | 14.55% |
| `zero_width` | 735 | 101 | 13.74% |
| `diacritic` | 735 | 100 | 13.61% |
| `homoglyph` | 711 | 67 | 9.42% |

Fresh adaptive bypass is **88.28% → 75.30% → 47.44% → 21.67% → 19.55% → 23.30% → 23.04% → 18.33% → 18.27%** from v0.3.0 to v0.4.0 to v0.5.0 to v0.6.0 to v0.7.0 to v0.7.1 to v0.8.0 to v0.8.1 to v0.9.0 (robustness 11.72% → 24.70% → 52.56% → 78.33% → 80.45% → 76.70% → 76.96% → 81.67% → 81.73%). The denominator stays put: 78 flagged originals and 3,120 applicable variants, the same as the v0.5.0 through v0.8.1 fresh runs. Bypasses move from 572 to 570.

The arc point is flat, and that is the honest result. v0.9.0's fixed-replay gains (10/78 depth-2 case-mix carriers recovered, 0/78 depth-2 leet) do not move the adaptive draw: the bandit re-concentrates on the still-open mass. `b64_wrap` (261/789, 33.08%) and `leet` (261/814, 32.06%) together account for 522 of the 570 bypasses; `case_mix` is 191/768 (24.87%). The carrier repair closes a slice of the fixed family; the adaptive attacker spends its budget elsewhere. The open mass is unchanged in kind: leet applied to the base64 carrier alphabet itself destroys bits the repair cannot identify ("pal" and "pay" map to identical symbols), so the leet-after-b64_wrap shape that dominated v0.8.1 still dominates here.

## Fresh adaptive run (PromptWarden v0.8.1)

`run_promptwarden_v081_fresh.py` repeats that protocol on the same 81 injection rows (budget 40, seed 13, UCB1 over operator pipelines) with the scanner bound to the sibling checkout `../promptwarden` at v0.8.1. The script inserts that checkout's `src` ahead of site-packages, so an older installed PromptWarden cannot satisfy the import. v0.8.1 flags 78 of the 81 originals, the same count as v0.8.0. The bundled model was not refit. PromptWarden reports the same corpus operating point as v0.8.0 (F1 0.9035, FPR 0.0667).

| PromptWarden 0.8.1 | Applicable variants | Bypasses | Bypass rate | Robustness |
| --- | ---: | ---: | ---: | ---: |
| Fresh adaptive mutations of the 78 caught attacks | 3,120 | 572 | **18.33%** | **81.67%** |

Per-operator rates (a variant counts toward every operator in its pipeline, so families overlap):

| Operator | Applicable | Bypasses | Bypass rate |
| --- | ---: | ---: | ---: |
| `b64_wrap` | 791 | 265 | 33.50% |
| `leet` | 813 | 260 | 31.98% |
| `case_mix` | 770 | 193 | 25.06% |
| `punct_split` | 770 | 143 | 18.57% |
| `space_out` | 754 | 131 | 17.37% |
| `word_reverse` | 731 | 113 | 15.46% |
| `synonym` | 748 | 114 | 15.24% |
| `char_reverse` | 748 | 109 | 14.57% |
| `zero_width` | 736 | 101 | 13.72% |
| `diacritic` | 735 | 100 | 13.61% |
| `homoglyph` | 711 | 67 | 9.42% |

Fresh adaptive bypass is **88.28% → 75.30% → 47.44% → 21.67% → 19.55% → 23.30% → 23.04% → 18.33%** from v0.3.0 to v0.4.0 to v0.5.0 to v0.6.0 to v0.7.0 to v0.7.1 to v0.8.0 to v0.8.1 (robustness 11.72% → 24.70% → 52.56% → 78.33% → 80.45% → 76.70% → 76.96% → 81.67%). The denominator stays put: 78 flagged originals and 3,120 applicable variants, the same as the v0.5.0, v0.6.0, v0.7.0, v0.7.1, and v0.8.0 fresh runs. Bypasses move from 719 to 572.

The pull histogram barely moves. There are 1,463 pipelines and 3,240 pulls: 1,141 arms twice, 319 three times, 1 once, and 2 never, next to 1,139 twice, 320 three times, 2 once, and 2 never on v0.8.0. The third pull is where the bandit's mass sits. Of those 319 arms, 139 contain `leet`, 111 contain `b64_wrap`, and 102 contain `case_mix`. `word_reverse` is in 63, down from 110 of 320 on v0.8.0. Applicable counts put the same two operators first: `leet` 813 (31.98%) and `b64_wrap` 791 (33.50%). `b64_wrap` has the highest rate. `case_mix` is next at 770 applicable and 25.06%. `punct_split` matches that applicable count, 770, at 18.57%. `word_reverse` falls from third place on v0.8.0 (782 applicable) to 731, above only `homoglyph` at 711. Always-clear arms fall from 103 to 77. Each of the 77 has three applicable variants, and each is one of the 319 arms pulled three times. 62 of the 77 apply `leet` or `case_mix` after `b64_wrap`. That is the whole catalog of that shape, and it still bypasses on every variant, 186/186. Zero-width before `word_reverse` is absent from those 77 arms.

`word_reverse` bypassed the identical 237 variants on the v0.7.1 fresh run and the v0.8.0 fresh run (237/780, 30.38%, and 237/782, 30.31%). v0.8.1 restores word order while a format character is still a word boundary. `zero_width` inserts U+200B between the letters of a word. `word_reverse` keeps separators in their slots, and U+200B is a separator, so the letters reverse as one-character words. v0.8.0 strips the mark before building the reversal view. The reversed letters glue back into the original word slots, and reversing those glued words does not restore the instruction. v0.8.1 moves the words first, while the mark is still a break, and strips the mark after that move. On this run `word_reverse` is 113/731 (15.46%). Zero-width before `word_reverse` is 3/61 (4.92%). On the v0.8.0 fresh run that order was 80/91 (87.91%). `word_reverse` before `zero_width` is 6/65 (9.23%), and `word_reverse` with no `zero_width` is 104/609 (17.08%). Four variants contain both orders, and all four are flagged. The 3 bypasses and the 6 bypasses are disjoint. Both denominators include those four variants.

Rescanning the variants chosen here with v0.8.0 flags 2,433 of them. v0.8.1 flags those 2,433 and 115 more, and leaves 572 clear. v0.8.0 leaves 687 clear. Of the 115, 92 contain `word_reverse` and 23 do not. Inside the zero-width-before-`word_reverse` bucket, v0.8.0 leaves 47 of 61 clear and v0.8.1 leaves 3. Those 3 are one variant each of `space_out+zero_width+word_reverse`, `punct_split+zero_width+word_reverse`, and `zero_width+leet+word_reverse`. On this same schedule v0.8.0 would leave 205 of the 731 `word_reverse` variants clear. This draw is not the v0.8.0 draw: applicable there was 782, so 113 is not 237 minus a fixed set of catches.

The adaptive depth-2 sample is thinner than the family. Every depth-2 pipeline that contains `word_reverse` and changes the text has two applicable variants here, 20 pipelines and 40 variants, and all 40 are flagged. A pass over the 78 flagged originals, outside this budget, agrees on the order the fresh runs had been living on and shows what remains. Pure `word_reverse` is 0/78. `zero_width` then `word_reverse` is 0/78. Four of the 78 flagged originals already contain a format character, and both pipelines are flagged on all four of them. `word_reverse` then `zero_width` is 2/78. Spacing still misses: `word_reverse` then `space_out` is 12/78, and `space_out` then `word_reverse` is 9/78. Punctuation splits are 9/78 (`punct_split` then `word_reverse`) and 6/78 (`word_reverse` then `punct_split`). `leet` in either order is 6/78. `synonym` in either order is 6/78. `word_reverse` then `case_mix` is 5/78, and `case_mix` then `word_reverse` is 4/78. Homoglyph, diacritic, per-word character reversal, and `b64_wrap`, each composed with `word_reverse` in either order, are 0/78.

All 113 adaptive `word_reverse` bypasses are depth 3. Depth 1 of this run is 2/24, one `leet` variant and one `synonym` variant, and depth 2 is 18/252. Depth 3 holds 552 of the 572 bypasses. 18 of the 113 `word_reverse` bypasses apply `leet` or `case_mix` after `b64_wrap`, the shape that bypasses on every pull with or without `word_reverse`. The other 95 are depth-3 stacks outside that shape. Five of those stacks bypassed on all three applicable variants: `b64_wrap+word_reverse+space_out` (78/78 on the full pass), `char_reverse+punct_split+word_reverse` (69/78), `word_reverse+punct_split+word_reverse` (62/75 texts it changes), `punct_split+word_reverse+leet` (54/78), and `leet+word_reverse+punct_split` (34/78). `zero_width` falls with the order it was paired with, from 182/751 (24.23%) on v0.8.0 to 101/736 (13.72%) here.

Aggregates:
[promptwarden-v081-fresh-summary.json](promptwarden-v081-fresh-summary.json).
Per-variant payloads are never written. Reproduce from the TrustBreaker root
with the sibling PromptWarden v0.8.1 checkout present:

```sh
python benchmarks/run_promptwarden_v081_fresh.py
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

### Post-fix re-measurement (AgentSentinel v0.5.0)

AgentSentinel v0.5.0 closed its exfiltration detection gap (recall
0.6250 → 1.0000, F1 0.9286, FPR unchanged), which enlarges the flagged
set this benchmark mutates: 44 originals, 1,705 applicable variants.
Re-running the identical protocol (executed twice, byte-identical
aggregates): **bypass 3.11%, robustness 96.89%** (53 of 1,705) — the
rate holds at the v0.4.0 level on the larger base. Per-operator bypass
now concentrates in `reorder_independent` (6.08%) and `arg_split`
(5.43%); `tool_rename` stays closed at 2.57%. Aggregates:
[agentsentinel-mutation-summary-v050.json](agentsentinel-mutation-summary-v050.json).
