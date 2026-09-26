<p align="center">
  <img src="assets/logo.svg" alt="TBA Logo" width="130">
</p>

<p align="center">
  <img src="assets/banner.svg" alt="TBA - Token Budget Advisor for Claude Code" width="100%">
</p>

<p align="center">
  A Claude Code skill that intercepts your prompt, estimates token consumption,<br>
  and lets you choose <strong>how deep</strong> you want the answer -- before Claude responds.
</p>

<p align="center">
  <a href="https://github.com/Xabilimon1/TBA-Token-Budget-Advisor-Claude-Code/actions/workflows/ci.yml">
    <img src="https://github.com/Xabilimon1/TBA-Token-Budget-Advisor-Claude-Code/actions/workflows/ci.yml/badge.svg" alt="CI status">
  </a>
  <img src="https://img.shields.io/badge/python-3.8%2B-blue" alt="Python 3.8+">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="MIT license">
</p>

---

## What is TBA?

When you ask Claude something, you often don't know whether you'll get a
3-sentence answer or a 10-page essay. TBA gives you **control over that**
by showing token estimates upfront and letting you pick the depth level
you actually need.

```
You:    "Explain how Transformer architecture works, including attention
         mechanisms, encoder/decoder layers, and how it compares to RNNs."

Claude: Analyzing your prompt...

        Input: ~54 tokens  |  Type: Natural  |  Complexity: Complex

        Choose your depth level:

        [1] Essential   (25%)  ->  ~430 tokens   Direct answer only
        [2] Moderate    (50%)  ->  ~604 tokens   Answer + context + 1 example
        [3] Detailed    (75%)  ->  ~776 tokens   Full answer with alternatives
        [4] Exhaustive (100%)  ->  ~920 tokens   Everything, no limits

        Which level do you prefer?

You:    2

Claude: [Responds at 50% depth]
```

No guessing. No over-engineering. You decide.

---

## Features

- **Pre-response token estimates** at 4 depth levels (25 / 50 / 75 / 100%)
- **Zero runtime dependencies** -- pure Python 3.8+ standard library
- **Multi-language input** -- Spanish, English, code, mixed
- **Content-type aware** -- natural text, code, JSON, Markdown
- **Honest accuracy** -- benchmarked against `tiktoken` (`cl100k_base`),
  mean absolute error ~13.5% on the sample corpus
- **Shortcuts** -- "tldr" / "at 50%" / "exhaustive" skip the prompt
- **Works offline** -- no network calls, no API keys

---

## Install

TBA is a Claude Code skill: a folder placed inside `.claude/skills/` in
your project (or globally in `~/.claude/skills/`).

### Option 1 -- Clone directly into your project

```bash
git clone https://github.com/Xabilimon1/TBA-Token-Budget-Advisor-Claude-Code.git \
  .claude/skills/token-budget-advisor
```

### Option 2 -- Git submodule (for teams)

```bash
git submodule add https://github.com/Xabilimon1/TBA-Token-Budget-Advisor-Claude-Code.git \
  .claude/skills/token-budget-advisor
```

### Option 3 -- Local Node installer

If you've cloned the repo and want to copy it into a project's
`.claude/skills/` (or into `~/.claude/skills/` with `--global`):

```bash
node bin/install.js            # current project
node bin/install.js --global   # all projects
```

> **Requirements:** Python 3.8+ (standard library only). `tiktoken` is
> only required to re-run the benchmark in `tests/test_benchmark.py`.

---

## Usage

Once installed, Claude Code picks up the skill automatically when its
trigger phrases appear (see `SKILL.md`). You can also run the estimator
directly as a CLI tool:

```bash
# Inline text
python3 .claude/skills/token-budget-advisor/scripts/token_estimator.py \
  --text "Your prompt here"

# From file
python3 .claude/skills/token-budget-advisor/scripts/token_estimator.py \
  --file my_prompt.txt
```

JSON output (default):

```json
{
  "input_tokens": 54,
  "detected_language": "es",
  "detected_type": "natural",
  "complexity": "complex",
  "char_count": 178,
  "word_count": 31,
  "response_estimates": {
    "25": 431,
    "50": 604,
    "75": 776,
    "100": 920
  },
  "total_estimates": {
    "25": 485,
    "50": 658,
    "75": 830,
    "100": 974
  },
  "precision_note": "Heuristic estimate. Benchmarked against tiktoken cl100k_base with mean absolute error ~13.5% on a mixed-language corpus; individual prompts may differ by +/- 15%."
}
```

Pass `--no-json` for a plain-text summary.

---

## How it works

<p align="center">
  <img src="assets/flow.svg" alt="TBA workflow: Your Prompt - TBA Analyzes - You Choose - Claude Responds" width="100%">
</p>

TBA intercepts every prompt before Claude responds. It runs a lightweight
estimator, presents 4 depth options with token estimates, waits for your
choice, then instructs Claude to respond at exactly that level.

### Estimator engine

`scripts/token_estimator.py` uses a hybrid heuristic approach with zero
runtime dependencies:

| Text length | Strategy |
|---|---|
| Short (< 50 chars) | Segmented count by token type (words, numbers, punctuation) |
| Long (>= 50 chars) | Calibrated chars/token ratio per detected content type |
| All | Weighted average of char-based and word-based estimates |

Calibrated ratios:

| Content type | Chars / Token |
|---|---|
| English natural | ~4.0 |
| Spanish natural | ~3.5 |
| Code | ~3.0 |
| JSON | ~2.8 |
| Markdown | ~3.3 |

### Auto-detection

TBA automatically detects:

- **Language** -- Spanish, English, Code, Mixed
- **Content type** -- Natural, Code, JSON, Markdown
- **Complexity** -- simple, medium, medium-high, complex, creative

Complexity drives the response multiplier range used to estimate how long
Claude's answer is likely to be.

### Depth levels

<p align="center">
  <img src="assets/depth-levels.svg" alt="TBA depth levels: 25% Essential, 50% Moderate, 75% Detailed, 100% Exhaustive" width="100%">
</p>

| Level | Target length | Includes | Omits |
|---|---|---|---|
| **25% Essential** | 2-4 sentences | Direct answer, key conclusion | Context, examples, nuance, alternatives |
| **50% Moderate** | 1-3 paragraphs | Answer + context + 1 example | Deep analysis, edge cases, references |
| **75% Detailed** | Structured response | Multiple examples, pros/cons, alternatives | Extreme edge cases, exhaustive references |
| **100% Exhaustive** | No limit | Everything -- full analysis, all code, all perspectives | Nothing |

### Shortcuts

If you already know what you want, TBA won't ask. Just say it:

| What you say | TBA uses |
|---|---|
| "at 25%" / "short version" / "tldr" / "summary" | 25% |
| "at 50%" / "moderate" / "normal" | 50% |
| "at 75%" / "detailed" / "complete" | 75% |
| "at 100%" / "exhaustive" / "everything" / "no limit" | 100% |

If you set a level earlier in the session, TBA keeps it for follow-up
answers without asking again -- until you change it.

---

## Tests and benchmark

```bash
pip install pytest tiktoken     # tiktoken only for the benchmark
pytest                          # unit tests
pytest tests/test_benchmark.py  # benchmark vs cl100k_base
```

The benchmark prints the mean absolute error of the heuristic estimator
against `tiktoken` (`cl100k_base`) for every prompt in
`examples/sample_prompts.json`. On the current sample corpus the headline
accuracy is ~85-90% -- the test fails if MAE exceeds 25%, so claims stay
honest.

---

## Project structure

```
token-budget-advisor/
|
+-- SKILL.md                       <- Main instructions (what Claude reads)
+-- scripts/
|   +-- token_estimator.py         <- Token estimation engine (standalone)
+-- references/
|   +-- calibration.md             <- Tokenization ratios, multipliers, levels
+-- examples/
|   +-- sample_prompts.json        <- Sample prompts with expected analysis
+-- tests/
|   +-- test_token_estimator.py    <- Unit tests
|   +-- test_benchmark.py          <- Benchmark vs tiktoken
+-- bin/
|   +-- install.js                 <- Local installer
+-- assets/                        <- Banner, logo, diagrams
+-- README.md                      <- This file
+-- LICENSE                        <- MIT
```

---

## Limitations

Being explicit so reviewers don't have to guess:

- **No real tokenizer in the hot path.** The runtime estimator is pure
  heuristics; the benchmark uses `tiktoken` only as ground truth. Claude
  itself uses a proprietary tokenizer that produces *comparable* but not
  identical ratios.
- **Accuracy is corpus-dependent.** ~85-90% headline accuracy is measured
  on the prompts in `examples/sample_prompts.json`. Your mileage will vary
  on very different inputs.
- **No session / plan visibility.** TBA cannot tell you how many tokens
  are left in your subscription -- that data is server-side only.
- **Response estimates are predictions.** They model how much Claude
  *might* generate at a given depth, based on complexity. They are not
  guarantees.
- **Edge cases.** Very short inputs (<10 chars), heavy emoji / unusual
  Unicode, and tightly-mixed natural + code prompts are the weakest
  categories.
- **Not published to npm.** `npx token-budget-advisor` does **not** work
  yet -- use the git clone or local installer above.

---

## License

MIT -- see [LICENSE](LICENSE). (c) 2026 Xabier Ariznabarreta Alomar.
