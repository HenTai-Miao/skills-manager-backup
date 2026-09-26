"""
Unit tests for the TBA token estimator.

These tests cover the public API of `scripts/token_estimator.py`:
- `analyze` (top-level pipeline)
- `estimate_tokens` (short + long path)
- `detect_language`
- `detect_content_type`
- `estimate_complexity`
- `estimate_response_tokens`
- Edge cases: empty string, emojis, very short input
"""

import json
from pathlib import Path

import pytest

from token_estimator import (
    analyze,
    detect_content_type,
    detect_language,
    estimate_complexity,
    estimate_response_tokens,
    estimate_tokens,
)

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PROMPTS = json.loads(
    (ROOT / "examples" / "sample_prompts.json").read_text(encoding="utf-8")
)


# ---------------------------------------------------------------------------
# estimate_tokens
# ---------------------------------------------------------------------------


def test_empty_string_returns_zero():
    assert estimate_tokens("") == 0


def test_short_text_returns_positive():
    # Short path (<50 chars)
    tokens = estimate_tokens("hello world")
    assert tokens > 0
    assert isinstance(tokens, int)


def test_long_text_returns_positive():
    # Long path (>=50 chars), English natural
    text = "This is a fairly long sentence designed to exercise the long-text branch of the estimator."
    tokens = estimate_tokens(text)
    assert tokens > 10


def test_long_text_scales_with_length():
    short = "This is a short English sentence used as a baseline." * 1
    long = short * 10
    assert estimate_tokens(long) > estimate_tokens(short) * 5


def test_emoji_heavy_input_does_not_crash():
    # Edge case from README's "Limitations" section
    text = "🚀🎉🔥💯✨" * 3
    tokens = estimate_tokens(text)
    assert tokens >= 1


# ---------------------------------------------------------------------------
# detect_language
# ---------------------------------------------------------------------------


def test_detect_language_english():
    text = "The quick brown fox jumps over the lazy dog and then keeps running."
    assert detect_language(text) == "en"


def test_detect_language_spanish():
    text = "El rápido zorro marrón salta sobre el perro perezoso y continúa corriendo por el bosque."
    assert detect_language(text) == "es"


def test_detect_language_code():
    text = "def foo(x): return x + 1\nconst y = 2;\nfunction bar() { return y; }"
    assert detect_language(text) in {"code", "mixed"}


def test_detect_language_unknown_for_pure_digits():
    assert detect_language("12345 67890") == "unknown"


# ---------------------------------------------------------------------------
# detect_content_type
# ---------------------------------------------------------------------------


def test_detect_content_type_json():
    assert detect_content_type('{"a": 1, "b": [2, 3]}') == "json"


def test_detect_content_type_code():
    text = (
        "def foo(x):\n"
        "    if x > 0:\n"
        "        return x * 2\n"
        "    return 0\n"
    )
    assert detect_content_type(text) == "code"


def test_detect_content_type_markdown():
    # Markdown-heavy text that does not trigger the code detector.
    # Bracket characters and `**` push up `code_score`, so we keep the
    # sample dense in headings + bullets and free of fenced blocks.
    text = (
        "# Hello\n\n"
        "A paragraph of text.\n\n"
        "## Subsection\n\n"
        "- one\n"
        "- two\n"
        "- three\n"
    )
    assert detect_content_type(text) == "markdown"


def test_detect_content_type_natural():
    assert detect_content_type("Just a sentence with no special syntax.") == "natural"


# ---------------------------------------------------------------------------
# estimate_complexity
# ---------------------------------------------------------------------------


def test_complexity_simple_short_question():
    label, lo, hi = estimate_complexity("What is X?")
    assert label == "simple"
    assert 0 < lo < hi


def test_complexity_complex_long_analysis():
    text = (
        "Compare and contrast microservices architecture vs monolithic architecture, "
        "including pros and cons, use cases, and implementation examples for each approach."
    )
    label, _, _ = estimate_complexity(text)
    assert label == "complex"


def test_complexity_creative():
    text = "Write a story about a robot that learns to imagine new characters."
    label, _, _ = estimate_complexity(text)
    assert label == "creative"


# ---------------------------------------------------------------------------
# estimate_response_tokens
# ---------------------------------------------------------------------------


def test_response_tokens_monotonic():
    levels = estimate_response_tokens(100, ("medium", 8, 20))
    assert levels["25"] < levels["50"] < levels["75"] < levels["100"]


def test_response_tokens_minimums_enforced():
    # Tiny input must still produce non-trivial response estimates.
    levels = estimate_response_tokens(1, ("simple", 3, 8))
    assert levels["25"] >= 30
    assert levels["50"] >= 100
    assert levels["75"] >= 250
    assert levels["100"] >= 400


# ---------------------------------------------------------------------------
# analyze (full pipeline)
# ---------------------------------------------------------------------------


def test_analyze_shape():
    result = analyze("Hello, world!")
    for key in (
        "input_tokens",
        "detected_language",
        "detected_type",
        "complexity",
        "char_count",
        "word_count",
        "response_estimates",
        "total_estimates",
        "precision_note",
    ):
        assert key in result, f"missing key: {key}"
    for level in ("25", "50", "75", "100"):
        assert level in result["response_estimates"]
        assert level in result["total_estimates"]
        assert result["total_estimates"][level] == (
            result["input_tokens"] + result["response_estimates"][level]
        )


def test_analyze_empty_string():
    result = analyze("")
    assert result["input_tokens"] == 0
    assert result["char_count"] == 0
    assert result["word_count"] == 0


@pytest.mark.parametrize("sample", SAMPLE_PROMPTS, ids=lambda s: f"prompt-{s['id']}")
def test_sample_prompts_match_expected(sample):
    """
    Run every prompt in `examples/sample_prompts.json` through analyze() and
    check that detected language / type / complexity match the curated
    expectations. This is the primary regression suite for the classifier.
    """
    result = analyze(sample["prompt"])
    expected = sample["expected"]
    assert result["detected_language"] == expected["language"], sample["notes"]
    assert result["detected_type"] == expected["type"], sample["notes"]
    assert result["complexity"] == expected["complexity"], sample["notes"]
