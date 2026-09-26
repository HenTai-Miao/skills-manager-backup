<!-- Plan template for branch-workflow projects. Used by /blueprint Phase 3. -->

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
{Properties that must hold after EVERY step completes. Verified before push.}
- All CI checks pass: `{build + test + lint + format commands}`
- {project-specific invariants}

## Branch & Merge Workflow

### Branch naming
- Format: `{project}-step-{NN}-{short-desc}` (kebab-case, e.g., `myapp-step-03-auth-module`)
- Always branch from latest default branch (detected in Phase 1 pre-flight): `git pull origin {default-branch} && git checkout -b <branch>`
- One branch per step. Never bundle multiple steps into one branch.

### Pre-push strongest-model review gate
Every branch must pass a strongest-model review before pushing to remote. No exceptions.
1. Executing agent completes all tasks and runs verification locally.
2. Executing agent commits all changes on the feature branch.
3. **Before `git push`**: delegate review to a strongest-model sub-agent. If the executing agent is already the strong model, self-review is acceptable — the gate's purpose is to ensure strongest-model scrutiny, not to require a separate agent. The agent must still perform a structured review against the same criteria.
   - Prompt: "Review all commits on branch `{branch}` against `{default-branch}`. Check: correctness, edge cases, consistency with existing code, CLAUDE.md compliance, security. Return a structured list of findings (critical / important / minor)."
   - If critical or important findings: fix, commit, re-review. Iterate until clean.
   - Minor findings: fix if trivial, otherwise log in Progress Log.
4. Only after review passes: `git push -u origin <branch>`.

### Post-push CI gate
After push, CI must pass before merge.
1. After push: `gh run list -b <branch> --limit 1` to find the CI run.
2. Wait for CI: `gh run watch <run-id>`. Never proceed while CI is pending.
3. If CI fails: diagnose locally → fix → commit → re-review (strongest-model gate) → push → wait for CI again. Never merge a red branch.
4. After CI is green: `gh pr create --title '{step title}' --body '{summary}'`. Then merge: `gh pr merge --squash --delete-branch`. If `gh pr merge` fails due to branch protection rules (required reviewers, pending PR-specific status checks, merge queue), report the blocker to the user and wait for resolution before proceeding. If pre-flight found no `gh` auth, this step is omitted entirely (plan uses direct workflow).
5. After merge: `git checkout {default-branch} && git pull origin {default-branch}`. Verify merge commit.

### Zero-tolerance CI policy
- A CI failure that reaches `main` is a **P0 construction incident** — permanent, public, damages project credibility.
- If a step's CI fails 3 times consecutively, **stop execution**. Report to user with: what failed, what was tried, root cause hypothesis.
- When sequencing multiple PR merges, verify CI passes at each stage before proceeding to the next.

## Agent Autonomy Boundary

Operations are classified by reversibility. Executing agents must respect these boundaries.

**Autonomous** (execute without asking):
- branch, add, commit, build, test, lint — all local and reversible

**User-confirmed** (ask before executing):
- push, PR create, PR merge, force operations (push --force, reset --hard, rebase), remote configuration changes, tag creation + push — all remote-visible or hard to reverse
- Confirm with user before the first push of each branch. Subsequent pushes to the same branch (e.g., after fixing CI) may proceed without re-confirmation.

**Sequencing with review gate** (branch-workflow plans):
1. Complete work + commit locally
2. Strongest-model review + fix findings
3. Ask user permission to push
4. Push to remote

## Prescription Calibration

Not all plan content carries the same level of constraint. Executing agents must respect these tiers:

- **Zero freedom** (exact commands, no deviation): branch naming, CI commands, merge procedure, security-sensitive operations. Copy and execute literally.
- **Low freedom** (approach specified, implementation flexible): step decomposition, test structure, module boundaries, structural/interface code snippets. Follow the intent; adapt details to fit the actual code.
- **High freedom** (goal only): implementation code, commit messages, PR prose. Executing agent decides.

## Steps

### Step {NN}: {title} [ ]

**Branch**: `{project}-step-{NN}-{short-desc}`
**Size**: S / M / L
**Isolation**: main-tree (default) / worktree (opt-in — only for genuinely risky steps; sub-agent worktree isolation is unreliable in practice, so prefer main-tree unless the step is destructive or exploratory)
**Agent**: default / strongest

**Context** (cold-start brief):
{Minimum background for an agent that has NOT read previous steps.
Must be self-contained with Design Decisions + Invariants.
If this step restructures code written by a prior step (e.g., lifting a variable out of a scope, changing function signatures, reordering pipeline stages), explicitly describe the refactoring range: which file, which function/block, what moves where. Without this, the executing agent will hit scope or reference errors with no guidance on how to resolve them.}

**Tasks**:
<!-- Tasks may be tagged [exact], [guided], or [open] to signal freedom level. Default is agent's judgment. -->
1. ...
2. ...

**Rollback**: {recovery strategy on failure — usually "discard worktree" or "revert commit"}

**Verification** (minimum coverage — executing agents should add boundary, round-trip, and edge-case tests beyond this list):
- [ ] Automated: `{exact commands}`
- [ ] Manual: `{action + expected result}` (only at E2E milestones)

**Exit criteria**: {specific, measurable, unambiguous}

---

## State Snapshot (optional)

{For plans where the system under construction evolves structurally across steps (e.g., a processing pipeline gains new stages, a module gains new exports, a config file accumulates entries), include an expected state snapshot after each step or after key milestones. This serves as a verification anchor — executing agents compare actual state against the snapshot to catch drift.

Example format for a pipeline-based system:
```
After Step 03: pipeline stages = [parse, validate, transform, emit]
After Step 05: pipeline stages = [parse, validate, normalize, transform, enrich, emit]
After Step 07: pipeline stages = [parse, validate, normalize, transform, enrich, schedule, emit]
```

Omit this section if the system structure is static across steps.}

## Dependency Graph

{ASCII diagram showing step dependencies}

**Parallelizable**: {list groups of steps that can run concurrently}

## Progress Log

This table is the single source of truth for execution state.

| Step | Status | Branch | PR  | Notes |
|------|--------|--------|-----|-------|
| 01   | [ ]    | —      | —   | —     |

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
3. If a step is `[>]`: check branch state. If branch exists with commits, assess completion against exit criteria. If no branch, treat as `[ ]`.
4. Read Review Log for context on past issues and decisions.
5. Resume from the first `[ ]` or `[>]` step. Do not re-execute `[x]` or `[SKIP]` steps.
