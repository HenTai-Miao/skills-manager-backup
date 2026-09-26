# Contributing

Contributions welcome. Three categories of useful contributions:

## 1. New language examples

The skill currently ships with TypeScript (Strapi), Go (Zentra), and Python (FastAPI/PMAI) examples. Pull requests for new stacks are welcome:

- Rust (matching the original X For You implementation language)
- Elixir / Phoenix
- C# / .NET
- Java / Spring

A new example should:

- Include the six interfaces (Source, Hydrator, Filter, Scorer, Selector, SideEffect)
- Include a working runner that executes the stages in the correct order with correct parallelism
- Include at least three tests: stage ordering, source parallelism, error tolerance
- Include a README explaining what the example demonstrates
- Be MIT licensed, attribute the X For You pattern in the README

## 2. New reference files

The skill loads reference files on demand. New deep dives that fit the skill's scope are welcome:

- A reference on offline / batch pipeline patterns
- A reference on cold-start handling for new users
- A reference on calibration techniques for multi-action probabilities
- A reference on A/B testing infrastructure for weight tuning

## 3. Bug fixes and clarifications

Bug reports and corrections to the documentation are always welcome. Open an issue or send a PR.

## What doesn't fit

- New ML model architectures. This skill is about pipeline plumbing, not model architecture. Reference an external resource for that.
- Production-grade infra. The examples are deliberately minimal; they show the pattern. Productionizing them (caching, observability, scaling) is per-org work.
- Trademark-using rebrandings. Don't fork this and call it "X-Algorithm-for-Strapi" or similar. The pattern is free; the brand is not.

## Code style

- TypeScript: Prettier defaults, no semicolons-required preference. Strict mode on.
- Go: `gofmt` clean.
- Python: Black formatting, type hints on all public functions.

## Tests

Every example must keep its tests green. CI is not yet set up; run them locally:

```
cd examples/strapi-content-feed && npm test
cd examples/zentra-go && go test ./pipeline/
cd examples/pmai-task-prioritizer && pytest
```

## License

By contributing, you agree your contribution is licensed MIT.
