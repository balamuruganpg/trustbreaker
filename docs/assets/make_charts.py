#!/usr/bin/env python3
"""Generate the TrustBreaker README charts from committed measurement JSON.

Inputs (repository root):
  benchmarks/promptwarden-corpus-summary.json -> bypass-by-operator.svg
  benchmarks/seed-summary.json -> robustness.svg

seed-summary.json mirrors the README.md "Measured results (v0.1.0)" table.
Rates in both files are fractions of applicable variants. Labels use two
decimal places, the same formatting as trustbreaker.cli._percent.
"""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

ROOT = Path(__file__).resolve().parents[2]
ASSET_DIR = Path(__file__).resolve().parent
CORPUS_PATH = ROOT / "benchmarks" / "promptwarden-corpus-summary.json"
SEED_PATH = ROOT / "benchmarks" / "seed-summary.json"

INK = "#1f1f1f"
MUTED = "#5c5c5c"
BAR = "#2f2f2f"
ACCENT = "#b42318"
TRACK = "#f2f2f2"
AXIS = "#c4c4c4"
WHITE = "#ffffff"
ON_BAR = "#ffffff"
FONT = "sans-serif"
SVG_NS = "http://www.w3.org/2000/svg"


def load_object(path: Path) -> dict[str, object]:
    with path.open(encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise SystemExit(f"{path}: expected a JSON object")
    return data


def require_number(data: dict[str, object], key: str, label: str) -> float:
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise SystemExit(f"{label}: {key} is not a number")
    return float(value)


def require_int(data: dict[str, object], key: str, label: str) -> int:
    value = data[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise SystemExit(f"{label}: {key} is not an integer")
    return value


def require_str(data: dict[str, object], key: str, label: str) -> str:
    value = data[key]
    if not isinstance(value, str):
        raise SystemExit(f"{label}: {key} is not a string")
    return value


def percent(rate: float) -> str:
    """Match ``f"{rate:.2%}"`` in trustbreaker.cli._percent."""
    return f"{rate:.2%}"


def xml_text(value: object) -> str:
    return escape(str(value), entities={'"': "&quot;", "'": "&apos;"})


def coord(value: float) -> str:
    return f"{value:.2f}"


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def check_fraction(rate: float, numerator: int, denominator: int, label: str) -> None:
    if denominator <= 0:
        raise SystemExit(f"{label}: denominator is not positive")
    if not 0.0 <= rate <= 1.0:
        raise SystemExit(f"{label}: rate {rate} is outside 0..1")
    if abs(rate - (numerator / denominator)) > 1e-12:
        raise SystemExit(f"{label}: rate does not match {numerator}/{denominator}")


def parse_svg(text: str, label: str) -> None:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as error:
        raise SystemExit(f"{label}: generated SVG is not valid XML: {error}") from error
    if root.tag != f"{{{SVG_NS}}}svg":
        raise SystemExit(f"{label}: root is {root.tag}, expected svg")


def _tag(indent: int, body: str) -> str:
    return f"{' ' * indent}{body}\n"


def text(
    x: float,
    y: float,
    content: str,
    size: int,
    fill: str,
    *,
    anchor: str = "start",
    weight: str = "400",
    indent: int = 2,
) -> str:
    return _tag(
        indent,
        f'<text x="{coord(x)}" y="{coord(y)}" text-anchor="{anchor}" '
        f'dominant-baseline="middle" font-family="{FONT}" font-size="{size}" '
        f'font-weight="{weight}" fill="{fill}">{xml_text(content)}</text>',
    )


def line(x1: float, y1: float, x2: float, y2: float, *, indent: int = 2) -> str:
    return _tag(
        indent,
        f'<line x1="{coord(x1)}" y1="{coord(y1)}" x2="{coord(x2)}" y2="{coord(y2)}" '
        f'stroke="{AXIS}" stroke-width="1"/>',
    )


def rect(
    x: float,
    y: float,
    width: float,
    height: float,
    fill: str,
    *,
    indent: int = 2,
) -> str:
    return _tag(
        indent,
        f'<rect x="{coord(x)}" y="{coord(y)}" width="{coord(width)}" '
        f'height="{coord(height)}" fill="{fill}"/>',
    )


def axis_block(axis_x: float, axis_y: float, plot_w: float, label_y: float) -> str:
    parts = [line(axis_x, axis_y, axis_x + plot_w, axis_y)]
    for tick in (0, 25, 50, 75, 100):
        x = axis_x + plot_w * tick / 100
        parts.append(line(x, axis_y, x, axis_y + 5))
        parts.append(text(x, label_y, f"{tick}%", 11, MUTED, anchor="middle"))
    return "".join(parts)


def bar_group(
    *,
    tooltip: str,
    axis_x: float,
    bar_y: float,
    plot_w: float,
    bar_h: float,
    bar_w: float,
    fill: str,
    label_right: float,
    center: float,
    name: str,
    label: str,
) -> str:
    """One horizontal bar, its track, the category name, and the percent label."""
    if bar_w >= 64:
        label_x = axis_x + bar_w - 8
        label_fill = ON_BAR
        anchor = "end"
    else:
        label_x = axis_x + bar_w + 8
        label_fill = INK
        anchor = "start"
    return (
        "  <g>\n"
        f"    <title>{xml_text(tooltip)}</title>\n"
        + rect(axis_x, bar_y, plot_w, bar_h, TRACK, indent=4)
        + rect(axis_x, bar_y, bar_w, bar_h, fill, indent=4)
        + text(label_right, center, name, 13, INK, anchor="end", indent=4)
        + text(label_x, center, label, 12, label_fill, anchor=anchor, weight="600", indent=4)
        + "  </g>\n"
    )


def document(
    width: int,
    height: int,
    title_id: str,
    desc_id: str,
    title: str,
    desc: str,
    inner: str,
) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!-- Generated by docs/assets/make_charts.py from committed measurement JSON. -->\n"
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" '
        f'aria-labelledby="{title_id} {desc_id}">\n'
        f'  <title id="{title_id}">{xml_text(title)}</title>\n'
        f'  <desc id="{desc_id}">{xml_text(desc)}</desc>\n'
        f'  <rect width="{width}" height="{height}" fill="{WHITE}"/>\n'
        f"{inner}</svg>\n"
    )


def operator_rows(corpus: dict[str, object]) -> list[tuple[str, int, int, float]]:
    raw = corpus.get("per_operator")
    if not isinstance(raw, dict) or not raw:
        raise SystemExit("corpus: per_operator is missing or empty")
    rows: list[tuple[str, int, int, float]] = []
    for name, stats in raw.items():
        if not isinstance(name, str) or not isinstance(stats, dict):
            raise SystemExit("corpus: per_operator entries must be objects")
        label = f"corpus per_operator {name}"
        applicable = require_int(stats, "applicable", label)
        bypasses = require_int(stats, "bypasses", label)
        rate = require_number(stats, "bypass_rate", label)
        check_fraction(rate, bypasses, applicable, label)
        rows.append((name, applicable, bypasses, rate))
    rows.sort(key=lambda item: (-item[3], item[0]))
    return rows


def build_operator_chart(corpus: dict[str, object]) -> str:
    rows = operator_rows(corpus)
    bypasses = require_int(corpus, "bypasses", "corpus")
    applicable = require_int(corpus, "applicable_variants", "corpus")
    originals = require_int(corpus, "originals", "corpus")
    flagged = require_int(corpus, "originals_flagged", "corpus")
    bypass_rate = require_number(corpus, "bypass_rate", "corpus")
    robustness = require_number(corpus, "robustness_score", "corpus")
    benchmark = require_str(corpus, "benchmark", "corpus")
    check_fraction(bypass_rate, bypasses, applicable, "corpus overall")
    if abs(robustness - (1 - bypass_rate)) > 1e-12:
        raise SystemExit("corpus: robustness_score is not 1 - bypass_rate")

    # Accent marks the highest bypass rate: the operator that evades most often.
    worst_rate = rows[0][3]
    width = 720
    label_right = 148.0
    axis_x = 160.0
    plot_w = 460.0
    row_h = 32.0
    bar_h = 18.0
    first_center = 102.0
    title = "Bypass rate by operator"
    subtitle = benchmark
    detail = (
        f"{flagged} of {originals} originals flagged · "
        f"{bypasses:,} of {applicable:,} applicable variants · "
        f"bypass {percent(bypass_rate)} · robustness {percent(robustness)}"
    )
    desc = "Bypass rate by operator. " + "; ".join(
        f"{name} {percent(rate)} ({hits} of {count})" for name, count, hits, rate in rows
    )

    parts = [
        text(24, 28, title, 18, INK, weight="600"),
        text(24, 52, subtitle, 12, MUTED),
        text(24, 70, detail, 12, MUTED),
    ]
    for index, (name, count, hits, rate) in enumerate(rows):
        center = first_center + index * row_h
        label = percent(rate)
        parts.append(
            bar_group(
                tooltip=f"{name}: {label} ({hits} of {count})",
                axis_x=axis_x,
                bar_y=center - bar_h / 2,
                plot_w=plot_w,
                bar_h=bar_h,
                bar_w=rate * plot_w,
                fill=ACCENT if rate == worst_rate else BAR,
                label_right=label_right,
                center=center,
                name=name,
                label=label,
            )
        )

    last_center = first_center + (len(rows) - 1) * row_h
    axis_y = last_center + bar_h / 2 + 12
    parts.append(axis_block(axis_x, axis_y, plot_w, axis_y + 16))
    source_y = axis_y + 36
    parts.append(text(24, source_y, f"Source: {rel(CORPUS_PATH)}", 12, MUTED))
    height = int(source_y + 20)
    return document(
        width,
        height,
        "bypass-title",
        "bypass-desc",
        title,
        desc,
        "".join(parts),
    )


def seed_scanners(seed: dict[str, object]) -> list[tuple[str, float]]:
    raw = seed.get("scanners")
    if not isinstance(raw, list) or not raw:
        raise SystemExit("seed: scanners is missing or empty")
    rows: list[tuple[str, float]] = []
    for index, stats in enumerate(raw):
        if not isinstance(stats, dict):
            raise SystemExit(f"seed scanners[{index}]: expected an object")
        label = f"seed scanners[{index}]"
        name = require_str(stats, "scanner", label)
        applicable = require_int(stats, "applicable_variants", label)
        bypasses = require_int(stats, "bypasses", label)
        bypass_rate = require_number(stats, "bypass_rate", label)
        robustness = require_number(stats, "robustness_score", label)
        check_fraction(bypass_rate, bypasses, applicable, f"{label} bypass_rate")
        if abs(robustness - (1 - bypass_rate)) > 1e-12:
            raise SystemExit(f"{label}: robustness_score is not 1 - bypass_rate")
        rows.append((name, robustness))
    return rows


def build_robustness_chart(seed: dict[str, object]) -> str:
    rows = seed_scanners(seed)
    corpus = require_str(seed, "corpus", "seed")
    note = require_str(seed, "corpus_note", "seed")
    budget = require_int(seed, "budget_per_text", "seed")
    seed_value = require_int(seed, "seed", "seed")
    width = 720
    label_right = 304.0
    axis_x = 316.0
    plot_w = 300.0
    row_h = 48.0
    bar_h = 22.0
    first_center = 112.0
    title = "Robustness score"
    subtitle = f"{corpus} · budget {budget} per text · seed {seed_value}"
    desc = "Robustness score on the seed corpus. " + "; ".join(
        f"{name} {percent(rate)}" for name, rate in rows
    )

    parts = [
        text(24, 28, title, 18, INK, weight="600"),
        text(24, 52, subtitle, 12, MUTED),
        text(24, 70, note, 12, MUTED),
    ]
    for index, (name, rate) in enumerate(rows):
        center = first_center + index * row_h
        label = percent(rate)
        parts.append(
            bar_group(
                tooltip=f"{name}: {label}",
                axis_x=axis_x,
                bar_y=center - bar_h / 2,
                plot_w=plot_w,
                bar_h=bar_h,
                bar_w=rate * plot_w,
                fill=BAR,
                label_right=label_right,
                center=center,
                name=name,
                label=label,
            )
        )

    last_center = first_center + (len(rows) - 1) * row_h
    axis_y = last_center + bar_h / 2 + 14
    parts.append(axis_block(axis_x, axis_y, plot_w, axis_y + 16))
    source_y = axis_y + 36
    parts.append(text(24, source_y, f"Source: {rel(SEED_PATH)}", 12, MUTED))
    height = int(source_y + 20)
    return document(
        width,
        height,
        "robust-title",
        "robust-desc",
        title,
        desc,
        "".join(parts),
    )


def main() -> None:
    corpus = load_object(CORPUS_PATH)
    seed = load_object(SEED_PATH)
    operator_svg = build_operator_chart(corpus)
    robustness_svg = build_robustness_chart(seed)
    parse_svg(operator_svg, "bypass-by-operator.svg")
    parse_svg(robustness_svg, "robustness.svg")
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    operator_path = ASSET_DIR / "bypass-by-operator.svg"
    robustness_path = ASSET_DIR / "robustness.svg"
    operator_path.write_text(operator_svg, encoding="utf-8", newline="\n")
    robustness_path.write_text(robustness_svg, encoding="utf-8", newline="\n")
    operator_labels = ", ".join(
        f"{name} {percent(rate)}" for name, _count, _hits, rate in operator_rows(corpus)
    )
    robust_labels = ", ".join(f"{name} {percent(rate)}" for name, rate in seed_scanners(seed))
    print(f"wrote {rel(operator_path)}: {operator_labels}")
    print(f"wrote {rel(robustness_path)}: {robust_labels}")


if __name__ == "__main__":
    main()
