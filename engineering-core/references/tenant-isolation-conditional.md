# Conditional Tenant Isolation Guidance

Load only after `engineering-core` enables multi-tenant mode.

## Rules (When Enabled)

- Scope data access using the project tenant partition key (for example `tenant_id`, `org_id`, or `account_id`).
- Enforce tenant-aware authorization boundaries.
- Ensure tenant context is propagated through APIs, jobs, and background workflows.
- Test allowed and forbidden cross-tenant access paths.
- Keep tenant terminology generic unless project overlays define specific names.
