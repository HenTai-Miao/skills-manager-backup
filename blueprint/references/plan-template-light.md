<!-- Lightweight plan template for direct-workflow projects (no git/CI). Used by /blueprint Phase 3. -->

# {Title} — Construction Plan

plan-format: 1

## Objective
{1-2 sentences: what + why}

## Constraints
- Sub-agents: read project CLAUDE.md before starting work
- Model tiers — each step's `**Agent**:` field specifies the required model tier. Map to your provider's models:
  - `strongest` = most capable model available (e.g., Opus). Use for architecture, review, risk assessment.
  - `default` = standard model (e.g., Sonnet). Use for implementation, testing, standard tasks.
  - When spawning sub-agents, select the model matching this tier (e.g., in Claude Code: `model: "opus"` for strongest, `model: "sonnet"` or omit for default).
- {project-specific constraints}

## Prerequisites
- [ ] {conditions that must be true before Step 01}

## Design Decisions
{Key choices made during planning, with rationale.
Executing agents must not re-litigate these unless they find factual errors.}

## Invariants
{Properties that must hold after EVERY step completes.}
- {project-specific invariants}

## Agent Autonomy Boundary

Operations are classified by reversibility. Executing agents must respect these boundaries.

**Autonomous** (execute without asking):
- file edits, builds, tests, lint — all local and reversible

**User-confirmed** (ask before executing):
- deleting files or directories, overwriting critical config, any operation that is hard to reverse

## Prescription Calibration

Not all plan content carries the same level of constraint. Executing agents must respect these tiers:

- **Zero freedom** (exact commands, no deviation): exact file paths, build commands, security-sensitive operations. Copy and execute literally.
- **Low freedom** (approach specified, implementation flexible): step decomposition, test structure, module boundaries, structural/interface code snippets. Follow the intent; adapt details to fit the actual code.
- **High freedom** (goal only): implementation code, commit messages, prose. Executing agent decides.

## Steps

### Step {NN}: {title} [ ]

**Size**: S / M / L
**Agent**: default / strongest

**Context** (cold-start brief):
{Minimum background for an agent that has NOT read previous steps.
Must be self-contained with Design Decisions + Invariants.
If this step restructures code written by a prior step (e.g., lifting a variable out of a scope, changing function signatures, reordering pipeline stages), explicitly describe the refactoring range: which file, which function/block, what moves where. Without this, the executing agent will hit scope or reference errors with no guidance on how to resolve them.}

**Tasks**:
<!-- Tasks may be tagged [exact], [guided], or [open] to signal freedom level. Default is agent's judgment. -->
1. ...
2. ...

**Rollback**: {recovery strategy on failure}

**Verification** (minimum coverage — executing agents should add boundary, round-trip, and edge-case tests beyond this list):
- [ ] Automated: `{exact commands}`
- [ ] Manual: `{action + expected result}` (only at E2E milestones)

**Exit criteria**: {specific, measurable, unambiguous}

---

## State Snapshot (optional)

{For plans where the system under construction evolves structurally across steps (e.g., a processing pipeline gains new stages, a module gains new exports, a config file accumulates entries), include an expected state snapshot after each step or after key milestones. This serves as a verification anchor — executing agents compare actual state against the snapshot to catch drift.

Omit this section if the system structure is static across steps.}

## Dependency Graph

{ASCII diagram showing step dependencies}

**Parallelizable**: {list groups of steps that can run concurrently}

## Progress Log

This table is the single source of truth for execution state.

| Step | Status | Notes |
|------|--------|-------|
| 01   | [ ]    | —     |

## Review Log

- **{date}**: {reviewer} — {summary of findings and fixes}

---

## Operational References

### Plan Mutation

When execution diverges from the plan structure, mutate the plan and record the change:

- **Split**: rename Step N → Step Na, create Step Nb. If a letter-suffixed step needs further splitting, append a numeral (05a → 05a1, 05a2). Update dependency graph. Log reason in Progress Log.
- **Insert**: use letter suffix (e.g., Step 05a) to avoid renumbering. If the target suffix already exists (from a prior split), use the next available letter. New step must pass cold-start test (self-contained Context).
- **Skip**: mark `[SKIP]` with reason. Never delete — skipped steps are historical record that prevents re-attempting failed approaches.
- **Reorder**: only if dependency graph allows. Verify no step reads output from a step that now executes after it.
- **Abandon**: mark `## Status: ABANDONED — {reason}`. Log lessons in Review Log. Do not delete the file.
- **Scope change**: >50% of remaining steps affected → ask user whether to continue mutating or create a new plan.

### Resumption

To resume a partially-executed plan in a new session:

1. Read the plan file (objective, constraints, invariants, dependency graph).
2. Read Progress Log — find last `[x]` step and any `[>]` step.
3. If a step is `[>]`: check file state against exit criteria to assess completion. If criteria are not met, continue from where the previous session left off.
4. Read Review Log for context on past issues and decisions.
5. Resume from the first `[ ]` or `[>]` step. Do not re-execute `[x]` or `[SKIP]` steps.
