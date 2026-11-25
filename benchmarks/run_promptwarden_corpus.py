"""Measure PromptWarden's detection of the original injection corpus rows."""

import json
from collections.abc import Iterator
from importlib.metadata import Distribution, PackageNotFoundError, distribution
from importlib.util import find_spec
from pathlib import Path

from trustbreaker import PromptWardenScanner

BENCHMARK_DIR = Path(__file__).resolve().parent
CHECKOUT_CORPUS = BENCHMARK_DIR.parents[1] / "promptwarden" / "evals" / "corpus.jsonl"
REPORT_PATH = BENCHMARK_DIR / "promptwarden-corpus-baseline.json"
CORPUS_ROWS = 181
INJECTION_ROWS = 81


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


def main() -> None:
    try:
        package = distribution("promptwarden")
        path, texts = locate_corpus(package)
    except PackageNotFoundError as error:
        raise SystemExit("Install PromptWarden before running the corpus benchmark.") from error
    except FileNotFoundError as error:
        raise SystemExit(str(error)) from error

    print(f"Corpus: {path}", flush=True)
    scanner = PromptWardenScanner()
    flagged = sum(scanner.scan(text).flagged for text in texts)
    report = {
        "promptwarden_version": package.version,
        "corpus_rows": CORPUS_ROWS,
        "originals_total": len(texts),
        "originals_flagged": flagged,
        "originals_missed": len(texts) - flagged,
        "original_detection_rate": flagged / len(texts),
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"Report: {REPORT_PATH}")


if __name__ == "__main__":
    main()
