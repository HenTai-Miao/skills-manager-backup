# Coding Style Core

## Core Rules

- Apply SOLID/DRY and keep logic readable.
- Prefer pragmatic, working changes over cosmetic churn.
- Remove dead code while touching nearby areas.
- Fix root causes rather than symptoms.

## File and Configuration Discipline

- Keep files focused; split when responsibilities drift.
- Soft limit: ~400 lines per code file, with
  justified exceptions.
- Never hardcode secrets; use environment configuration.
- Fail loudly on missing required configuration.
- Preserve predictable repository structure and naming.

## Collaboration Conventions

- Use clear but concise commit/PR descriptions.
- Keep dependency surface minimal and documented.
- Define testing expectations before merge.
- Maintain release notes/changelog entries for significant changes.

## Commenting

- Prefer self-documenting code.
- Use comments for non-obvious rationale, not narration.
- Keep comments evergreen; avoid temporary-change commentary.
