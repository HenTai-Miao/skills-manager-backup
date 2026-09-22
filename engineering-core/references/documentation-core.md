# Documentation Standards Core

## What to Document

- Complex business logic and non-obvious decisions.
- API contracts and data model choices.
- Integration behavior, data transformations, and security-sensitive flows.
- Performance tradeoffs and deferred work.

## What Not to Document

- Self-evident assignments and simple boilerplate.
- Standard library usage without customization.
- Transient operational notes that belong in chat.

## Quality Workflow

- Update docs alongside behavioral changes.
- Remove stale TODOs and outdated examples.
- Review docs in code review.
- Keep a lightweight checklist for public APIs, error paths, and security-relevant behavior.

## Compliance Note

- Apply regulation-specific documentation only when the project explicitly requires a named compliance regime.
