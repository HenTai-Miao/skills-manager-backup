# Error Handling Core

## Principles

- Return user-safe, actionable messages without exposing internals.
- Fail fast on invalid input and unmet preconditions.
- Use specific error categories/types for targeted handling.
- Handle errors at clear boundaries.
- Degrade gracefully when non-critical dependencies fail.

## Resilience

- Use retries with bounded backoff for transient failures.
- Clean up resources on failure paths.
- Use correlation identifiers for logs/traces/responses.
- Prevent sensitive data leakage in error bodies and logs.

## Contract Discipline

- Keep API error contracts consistent and versioned.
- Show field-level error details when validation fails.
- Document any additive or breaking error contract changes.
