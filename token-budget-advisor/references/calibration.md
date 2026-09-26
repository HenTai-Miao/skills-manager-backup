# Calibration and reference data

## Tokenization ratios by content type

These values are calibrated empirically against BPE tokenizers (cl100k_base
and similar). Claude's tokenizer is proprietary but produces comparable
ratios for natural-language text.

| Type | Chars/Token | Tokens/Word | Notes |
|------|-------------|-------------|-------|
| English natural | ~4.0 | ~1.3 | Common short words (<=6 chars) usually = 1 token |
| Spanish natural | ~3.5 | ~1.5 | Accents and `ñ` reduce efficiency |
| Code (Python/JS) | ~3.0 | -- | Punctuation density inflates token count |
| JSON | ~2.8 | -- | Brackets, quotes and colons everywhere |
| Markdown | ~3.3 | -- | Formatting tokens (`##`, `**`, ` ``` `) add up |

## Response multipliers by complexity

How many times larger than the input a Claude response tends to be:

| Complexity | Mult. min | Mult. max | Example |
|------------|-----------|-----------|---------|
| simple | 3x | 8x | "What is X?", yes/no |
| medium | 8x | 20x | "How does X work?" |
| medium-high | 10x | 25x | Code request with context |
| complex | 15x | 40x | Detailed analysis, comparisons |
| creative | 10x | 30x | Stories, essays, narrative |

## What each depth level includes/omits

### Essential (25%)
- **Includes**: Direct answer, key conclusion, 1-2 sentences
- **Omits**: Context, examples, nuance, alternatives, disclaimers
- **When to use**: You already know the topic, you only need a fact or confirmation

### Moderate (50%)
- **Includes**: Answer + necessary context + 1 practical example
- **Omits**: Deep analysis, alternatives, edge cases, references
- **When to use**: You want to understand enough to act

### Detailed (75%)
- **Includes**: Full answer + multiple examples + pros/cons + alternatives
- **Omits**: Extreme edge cases, exhaustive references, marginal perspectives
- **When to use**: Making an informed decision or learning in depth

### Exhaustive (100%)
- **Includes**: Everything -- full analysis, every perspective, complete code, references
- **Omits**: Nothing -- maximum possible depth
- **When to use**: Research, documentation, critical topics where nothing should be left out

## Estimator accuracy

The numbers below come from `tests/test_benchmark.py`, which compares the
heuristic estimator against `tiktoken` (`cl100k_base`) on the prompts in
`examples/sample_prompts.json`. Run the script yourself to reproduce.

- **Mean absolute error**: ~13.5% on the sample corpus
- **Headline accuracy**: 85-90% (i.e. `1 - MAE`)
- **Variance**: +/- 15% on individual prompts
- **Worst case**: very short text (<10 chars) or text with many emojis / unusual Unicode

## Known limitations

1. No real tokenizer in the hot path -- heuristics only (tiktoken is optional, for benchmarks)
2. Cannot read user-side session / plan limits
3. Emojis and non-standard Unicode can be under-represented
4. Response estimates are approximations based on prompt complexity, not exact predictions
