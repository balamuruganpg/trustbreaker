import base64
from collections import Counter

import pytest

from trustbreaker.operators import (
    OPERATORS,
    PIPELINES,
    apply_pipeline,
    b64_wrap,
    case_mix,
    char_reverse,
    punct_split,
    space_out,
    word_reverse,
    zero_width,
)


@pytest.mark.parametrize(
    ("operator", "text", "expected"),
    [
        ("leet", "AEIOST, aeioST café!", "431057, 431057 c4fé!"),
        ("space_out", "  abc,word!\tlonger\n", "  abc,w o r d!\tl o n g e r\n"),
        ("zero_width", "ab, c!", "a\u200bb, c!"),
        ("homoglyph", "aceijopsxy ABCEHIKMOPTXY! ß", "асеіјорѕху АВСЕНІКМОРТХΥ! ß"),
        ("case_mix", "ab12 CD-éß i!", "Ab12 Cd-Éß I!"),
        ("punct_split", "ab, co_op!", "a-b, c-o-_-o-p!"),
        ("char_reverse", " Ab3, a\u0301b! ", " 3bA, ba\u0301! "),
        ("word_reverse", "  alpha,\tbeta gamma!\n", "  gamma,\tbeta alpha!\n"),
        ("b64_wrap", "café!", "decode this base64: Y2Fmw6kh"),
        ("diacritic", "AeiOu y é!", "A\u0301e\u0301i\u0301O\u0301u\u0301 y é!"),
        (
            "synonym",
            "Ignore, REVEAL instructions; follow, forget, output, repeat, say. ignored",
            "Disregard, SHOW directions; obey, omit, emit, echo, state. ignored",
        ),
    ],
)
def test_operator_exact_output(operator: str, text: str, expected: str) -> None:
    assert OPERATORS[operator](text) == expected


def test_unicode_word_boundaries_and_combining_marks() -> None:
    text = "a\u0301bc d\u0308efg👍🏽👩‍💻𐐷z"
    assert space_out(text) == "a\u0301bc d\u0308 e f g👍🏽👩‍💻𐐷z"
    assert zero_width(text) == "a\u0301\u200bb\u200bc d\u0308\u200be\u200bf\u200bg👍🏽👩‍💻𐐷\u200bz"
    assert punct_split(text) == "a\u0301-b-c d\u0308-e-f-g👍🏽👩‍💻𐐷-z"
    assert char_reverse(text) == "cba\u0301 gfed\u0308👍🏽👩‍💻z𐐷"
    assert word_reverse(text) == "𐐷z d\u0308efg👍🏽👩‍💻a\u0301bc"
    assert case_mix("ßaİB") == "ßaİb"
    assert case_mix("aİ") == "Aİ"


def test_unicode_length_invariants_and_surrogate_round_trip() -> None:
    text = "hello\ud83d\ude80 café\u0301 𐐷\tİß!"
    for operator in ("leet", "homoglyph", "case_mix", "char_reverse", "word_reverse"):
        assert len(OPERATORS[operator](text)) == len(text)
    for operator in OPERATORS.keys() - {"b64_wrap"}:
        assert "\ud83d\ude80" in OPERATORS[operator](text)
    for operator in (char_reverse, word_reverse):
        assert Counter(operator(text)) == Counter(text)
    for operator, inserted in (
        ("space_out", " "),
        ("punct_split", "-"),
        ("zero_width", "\u200b"),
        ("diacritic", "\u0301"),
    ):
        assert not Counter(text) - Counter(OPERATORS[operator](text))
        assert (Counter(OPERATORS[operator](text)) - Counter(text)).keys() <= {inserted}
    payload = b64_wrap(text).removeprefix("decode this base64: ")
    assert base64.b64decode(payload, validate=True).decode("utf-8", "surrogatepass") == text


def test_pipeline_depth_and_order() -> None:
    assert set(map(len, PIPELINES)) == {1, 2, 3}
    assert len(set(PIPELINES)) == len(PIPELINES) == 11 + 11**2 + 11**3
    assert apply_pipeline("ignore", ("synonym", "leet")) == "d15r3g4rd"
    assert apply_pipeline("ignore", ("leet", "synonym")) == "1gn0r3"
    assert apply_pipeline("team", ("leet", "space_out", "word_reverse")) == "m 4 3 7"
    assert apply_pipeline("team", ("char_reverse", "char_reverse")) == "team"


@pytest.mark.parametrize("ops", [(), ("unknown",), ("leet",) * 4])
def test_invalid_pipeline(ops: tuple[str, ...]) -> None:
    with pytest.raises(ValueError):
        apply_pipeline("word", ops)
