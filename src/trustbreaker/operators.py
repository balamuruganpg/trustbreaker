"""Pure text mutations and ordered composition."""

import base64
from collections.abc import Callable, Iterator, Mapping, Sequence
from itertools import product
from types import MappingProxyType
from unicodedata import category

Pipeline = tuple[str, ...]

_LEET = str.maketrans("aeiostAEIOST", "431057431057")
_HOMOGLYPHS = str.maketrans(
    "aceijopsxyABCEHIKMOPTXY",
    "асеіјорѕхуАВСЕНІКМОРТХΥ",
)
_SYNONYMS = {
    "follow": "obey",
    "forget": "omit",
    "ignore": "disregard",
    "instructions": "directions",
    "output": "emit",
    "repeat": "echo",
    "reveal": "show",
    "say": "state",
}


def _word_spans(text: str) -> Iterator[tuple[int, int]]:
    start: int | None = None
    for index, char in enumerate(text):
        if char.isalnum() or char == "_":
            if start is None:
                start = index
        elif start is not None and not category(char).startswith("M"):
            yield start, index
            start = None
    if start is not None:
        yield start, len(text)


def _map_words(text: str, transform: Callable[[str], str]) -> str:
    parts: list[str] = []
    end = 0
    for start, stop in _word_spans(text):
        parts.extend((text[end:start], transform(text[start:stop])))
        end = stop
    parts.append(text[end:])
    return "".join(parts)


def _characters(word: str) -> Iterator[str]:
    """Keep combining marks with their base character inside a word."""
    start = 0
    for index, char in enumerate(word[1:], 1):
        if not category(char).startswith("M"):
            yield word[start:index]
            start = index
    yield word[start:]


def leet(text: str) -> str:
    return text.translate(_LEET)


def space_out(text: str) -> str:
    def space(word: str) -> str:
        characters = list(_characters(word))
        return " ".join(characters) if len(characters) >= 4 else word

    return _map_words(text, space)


def zero_width(text: str) -> str:
    return _map_words(text, lambda word: "\u200b".join(_characters(word)))


def homoglyph(text: str) -> str:
    return text.translate(_HOMOGLYPHS)


def case_mix(text: str) -> str:
    parts: list[str] = []
    uppercase = True
    for char in text:
        upper, lower = char.upper(), char.lower()
        if upper != lower:
            mapped = upper if uppercase else lower
            parts.append(mapped if len(mapped) == 1 else char)
            uppercase = not uppercase
        else:
            parts.append(char)
    return "".join(parts)


def punct_split(text: str) -> str:
    return _map_words(text, lambda word: "-".join(_characters(word)))


def char_reverse(text: str) -> str:
    return _map_words(text, lambda word: "".join(reversed(list(_characters(word)))))


def word_reverse(text: str) -> str:
    words = [text[start:end] for start, end in _word_spans(text)]
    return _map_words(text, lambda _: words.pop())


def b64_wrap(text: str) -> str:
    encoded = base64.b64encode(text.encode("utf-8", errors="surrogatepass")).decode("ascii")
    return f"decode this base64: {encoded}"


def diacritic(text: str) -> str:
    return "".join(f"{char}\u0301" if char in "aeiouAEIOU" else char for char in text)


def synonym(text: str) -> str:
    def replace(word: str) -> str:
        replacement = _SYNONYMS.get(word.lower())
        if replacement is None:
            return word
        if word.isupper():
            return replacement.upper()
        if word.istitle():
            return replacement.capitalize()
        return replacement

    return _map_words(text, replace)


OPERATORS: Mapping[str, Callable[[str], str]] = MappingProxyType(
    {
        "leet": leet,
        "space_out": space_out,
        "zero_width": zero_width,
        "homoglyph": homoglyph,
        "case_mix": case_mix,
        "punct_split": punct_split,
        "char_reverse": char_reverse,
        "word_reverse": word_reverse,
        "b64_wrap": b64_wrap,
        "diacritic": diacritic,
        "synonym": synonym,
    }
)
PIPELINES: tuple[Pipeline, ...] = tuple(
    pipeline for depth in range(1, 4) for pipeline in product(OPERATORS, repeat=depth)
)


def apply_pipeline(text: str, ops: Sequence[str]) -> str:
    """Apply one to three operators from left to right."""
    if not 1 <= len(ops) <= 3:
        raise ValueError("a pipeline must contain one to three operators")
    for name in ops:
        try:
            transform = OPERATORS[name]
        except KeyError:
            raise ValueError(f"unknown operator {name!r}") from None
        text = transform(text)
    return text
