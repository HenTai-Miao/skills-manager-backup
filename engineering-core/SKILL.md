---
name: engineering-core
description: use for cross-cutting engineering rules that are language/framework-agnostic, including communication, verification, validation, dependency choices, documentation quality, and feature lifecycle discipline.
---

# Intent

Single source-of-truth for reusable engineering guidance across projects.

## Activation Rules

- Default: single-tenant, no special regulatory regime.
- Enable tenant-specific guidance only when user requests multi-tenant behavior or repo evidence shows multi-tenant architecture.
- Enable regulation/compliance guidance only when user requests specific regime or repo docs/config declare compliance requirements.
- Do not add tenant/compliance overhead without those signals.

## Workflow

1. Load `references/communication.md` and `references/coding-style-core.md` for baseline execution quality.
2. Load `references/verification-core.md` and `references/validation-core.md` when changing behavior.
3. Load `references/dependencies-core.md` when adding/updating third-party tooling.
4. Load `references/documentation-core.md` when producing/updating docs.
5. Load `references/error-handling-core.md` when defining/revising failure behavior.
6. Let the active task specialist own workflow and stop conditions.
7. When behavior changes, sync affected contracts, docs, and telemetry; define rollback when risk warrants.
8. Load `references/feature-removal.md` for deletion/sunset work.
9. Load `references/analytics-monitoring-core.md` only when telemetry/observability touched.
10. Load `references/tenant-isolation-conditional.md` only when tenant guidance enabled.
11. Load `references/compliance-conditional.md` only when compliance guidance enabled.
12. Load `references/human-decision-points.md` when a listed escalation trigger occurs.
13. If task includes Postgres DB/schema/migration/query design, use the installed
    `supabase-postgres-best-practices` specialist before final implementation decisions.

## Multi-Tenant Detection Signals

Treat multi-tenant as enabled only with concrete evidence:
- tenant partition keys (`tenant_id`, `account_id`, `org_id`, similar)
- tenant context helpers/middleware
- tenant context headers
- tenant-scoped authorization/policies
- row-level tenant isolation rules
