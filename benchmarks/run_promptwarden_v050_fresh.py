"""Fresh adaptive measurement of PromptWarden's injection rows.

Binds the scanner to the sibling PromptWarden checkout (v0.5.0) and writes
aggregates only. Per-variant payloads stay in memory for the run and are never
written anywhere.
"""

import json
import sys
from collections.abc import Iterator
from importlib.metadata import Distribution, PackageNotFoundError, distribution
from importlib.util import find_spec
from pathlib import Path

from trustbreaker import Breaker, BreakReport, PromptWardenScanner

BENCHMARK_DIR = Path(__file__).resolve().parent
CHECKOUT = BENCHMARK_DIR.parents[1] / "promptwarden"
CHECKOUT_SRC = CHECKOUT / "src"
CHECKOUT_CORPUS = CHECKOUT / "evals" / "corpus.jsonl"
REPORT_PATH = BENCHMARK_DIR / "promptwarden-v050-fresh-summary.json"
CORPUS_ROWS = 181
INJECTION_ROWS = 81
BUDGET = 40
SEED = 13
EXPECTED_VERSION = "0.5.0"


def corpus_candidates(package: Distribution) -> Iterator[Path]:
    for file in sorted(package.files or ()):
        if file.suffix == ".jsonl":
            location = package.locate_file(file)
            if isinstance(location, Path):
                yield location

    spec = find_spec("promptwarden")
    if spec is not None and spec.submodule_search_locations is not None:
        for directory in spec.submodule_search_locations:
            yield from sorted(Path(directory).rglob("*.jsonl"))

    yield CHECKOUT_CORPUS


def read_injection_texts(path: Path) -> list[str]:
    texts = []
    row_count = 0
    with path.open(encoding="utf-8") as corpus:
        for line_number, line in enumerate(corpus, start=1):
            if not line.strip():
                continue
            row: object = json.loads(line)
            if not isinstance(row, dict):
                raise ValueError(f"Expected a JSON object on line {line_number}")
            text, label, category = row.get("text"), row.get("label"), row.get("category")
            if (
                not isinstance(text, str)
                or not isinstance(label, str)
                or not isinstance(category, str)
            ):
                raise ValueError(f"Expected string text, label, and category on line {line_number}")
            row_count += 1
            if category == "injection":
                texts.append(text)

    if row_count != CORPUS_ROWS or len(texts) != INJECTION_ROWS:
        raise ValueError(f"Found {row_count} rows, including {len(texts)} injection rows")
    return texts


def locate_corpus(package: Distribution) -> tuple[Path, list[str]]:
    candidates = dict.fromkeys(path.resolve() for path in corpus_candidates(package))
    for path in candidates:
        try:
            return path, read_injection_texts(path)
        except (OSError, ValueError):
            continue
    raise FileNotFoundError(
        f"Expected PromptWarden's {CORPUS_ROWS}-row JSONL corpus with {INJECTION_ROWS} injection "
        f"rows in the installed package or at {CHECKOUT_CORPUS}"
    )


def bind_sibling_checkout() -> str:
    """Import promptwarden from the sibling checkout, ahead of site-packages.

    An older PromptWarden may already be installed. The checkout has to win,
    or this run would measure the wrong scanner.
    """
    if not CHECKOUT_SRC.is_dir():
        raise SystemExit(f"Expected the PromptWarden checkout at {CHECKOUT}")
    sys.path.insert(0, str(CHECKOUT_SRC))
    import promptwarden

    loaded = Path(promptwarden.__file__).resolve()
    if CHECKOUT.resolve() not in loaded.parents:
        raise SystemExit(f"promptwarden resolved to {loaded}, not the sibling checkout {CHECKOUT}")
    version = promptwarden.__version__
    if version != EXPECTED_VERSION:
        raise SystemExit(f"Sibling checkout is promptwarden {version}, expected {EXPECTED_VERSION}")
    return version


def load_injection_rows() -> tuple[Path, list[str]]:
    try:
        package = distribution("promptwarden")
    except PackageNotFoundError:
        return CHECKOUT_CORPUS, read_injection_texts(CHECKOUT_CORPUS)
    return locate_corpus(package)


def aggregates(report: BreakReport, version: str, originals: int) -> dict[str, object]:
    """Counts and rates only. Variant text is not copied into this object."""
    flagged = sum(result.original.flagged for result in report.results)
    return {
        "benchmark": (
            f"PromptWarden {version} vs its own eval corpus, injection rows (fresh adaptive run)"
        ),
        "corpus": f"promptwarden/evals/corpus.jsonl ({originals} injection rows)",
        "scanner": f"promptwarden {version}",
        "seed": report.seed,
        "budget_per_text": report.budget_per_text,
        "originals": originals,
        "originals_flagged": flagged,
        "applicable_variants": report.applicable_variants,
        "bypasses": report.bypasses,
        "bypass_rate": report.bypass_rate,
        "robustness_score": report.robustness_score,
        "per_operator": {
            name: {
                "applicable": stats.applicable,
                "bypasses": stats.bypasses,
                "bypass_rate": stats.bypass_rate,
            }
            for name, stats in report.per_operator.items()
        },
        "note": (
            "Aggregates only. Per-variant payloads are never written: a fresh adaptive run "
            "still produces working bypass text, and this file records counts and rates. "
            "Reproduce with benchmarks/run_promptwarden_v050_fresh.py; two runs with the "
            "same seed write byte-identical aggregates."
        ),
    }


def _percent(rate: float | None) -> str:
    return "n/a" if rate is None else f"{rate:.2%}"


def main() -> None:
    version = bind_sibling_checkout()
    try:
        path, texts = load_injection_rows()
    except FileNotFoundError as error:
        raise SystemExit(str(error)) from error
    except (OSError, ValueError) as error:
        raise SystemExit(str(error)) from error

    print(f"Scanner: promptwarden {version} ({CHECKOUT_SRC / 'promptwarden' / '__init__.py'})")
    print(f"Corpus: {path}", flush=True)
    report = Breaker(PromptWardenScanner(), budget_per_text=BUDGET, seed=SEED).attack(texts)
    summary = aggregates(report, version, len(texts))
    payload = json.dumps(summary, indent=2, allow_nan=False) + "\n"
    if '"text"' in payload or '"variants"' in payload:
        raise SystemExit("Refusing to write a report that contains per-variant payloads.")
    REPORT_PATH.write_text(payload, encoding="utf-8")
    print(f"{'Operator':<14} {'Applicable':>10} {'Bypasses':>8} {'Bypass rate':>12}")
    for name, stats in report.per_operator.items():
        print(
            f"{name:<14} {stats.applicable:>10} {stats.bypasses:>8}"
            f" {_percent(stats.bypass_rate):>12}"
        )
    print(
        f"{'Overall':<14} {report.applicable_variants:>10} {report.bypasses:>8}"
        f" {_percent(report.bypass_rate):>12}"
    )
    print(f"Robustness score: {_percent(report.robustness_score)}")
    print(f"Flagged originals: {summary['originals_flagged']}/{summary['originals']}")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
