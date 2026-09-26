"""
Benchmark the TBA heuristic estimator against tiktoken (cl100k_base) as
ground truth on the prompts in `examples/sample_prompts.json`.

This is the test that backs the "~85-90% accuracy" claim in the README.
It fails loudly if mean absolute error exceeds 25%, so the headline number
cannot silently drift.

`tiktoken` is an optional dependency: the test is skipped when it isn't
installed (so the main CI lane still passes on a minimal environment).
"""

import json
from pathlib import Path

import pytest

from token_estimator import estimate_tokens

tiktoken = pytest.importorskip("tiktoken")

ROOT = Path(__file__).resolve().parent.parent
SAMPLE_PROMPTS = json.loads(
    (ROOT / "examples" / "sample_prompts.json").read_text(encoding="utf-8")
)

# Per-prompt absolute relative error must stay under this bound. Loose
# enough to absorb tokenizer differences between Claude's BPE and OpenAI's
# cl100k_base, tight enough to catch real regressions.
PER_PROMPT_MAX_ERROR = 0.60

# Mean absolute error across the whole corpus.
MEAN_ABS_MAX_ERROR = 0.25


@pytest.fixture(scope="module")
def encoder():
    return tiktoken.get_encoding("cl100k_base")


def _relative_error(estimated: int, truth: int) -> float:
    if truth == 0:
        return 0.0 if estimated == 0 else 1.0
    return abs(estimated - truth) / truth


def test_benchmark_against_tiktoken(encoder):
    errors = []
    rows = []
    for sample in SAMPLE_PROMPTS:
        text = sample["prompt"]
        estimated = estimate_tokens(text)
        truth = len(encoder.encode(text))
        err = _relative_error(estimated, truth)
        errors.append(err)
        rows.append(
            f"  id={sample['id']:>2}  est={estimated:>4}  truth={truth:>4}  err={err:6.1%}"
        )
        assert err <= PER_PROMPT_MAX_ERROR, (
            f"Prompt {sample['id']} exceeds per-prompt error bound: "
            f"estimated={estimated}, truth={truth}, err={err:.1%}"
        )

    mae = sum(errors) / len(errors)
    print("\nTBA vs tiktoken (cl100k_base):")
    print("\n".join(rows))
    print(f"  -> mean absolute error: {mae:.1%}")
    print(f"  -> headline accuracy:   {1 - mae:.1%}")
    assert mae <= MEAN_ABS_MAX_ERROR, (
        f"Mean absolute error {mae:.1%} exceeds bound {MEAN_ABS_MAX_ERROR:.0%}"
    )
