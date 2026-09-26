# Execution Resumption Protocol

When resuming a partially-executed plan in a new session, follow these steps in order. The goal is to reconstruct execution state from the plan file alone — no prior conversation history required.

## Resumption Procedure

1. **Read the plan file.** Understand the objective, constraints, invariants, and dependency graph. Note the workflow mode (branch vs. direct).

2. **Read the Progress Log.** Identify:
   - The last completed step (status `[x]`)
   - Any in-progress step (status `[>]`)
   - Any skipped steps (status `[SKIP]`) — do not re-attempt these

3. **Assess in-progress steps.** If a step is marked `[>]`:
   - Check whether its branch exists: `git branch --list '{branch-name}'` (local) or `git ls-remote --heads origin '{branch-name}'` (remote). Use exact name match, not substring grep.
   - If the branch **exists with commits**: read those commits and assess how much work is done. Determine whether the step is near-complete or needs significant remaining work.
   - If the branch **does not exist** (or has no commits): treat the step as `[ ]` (not started) and begin from scratch.

4. **Read the Review Log.** Note any past findings, blockers, or decisions made during prior execution sessions. These provide context for why certain approaches were taken or avoided.

5. **Resume from the first `[ ]` or `[>]` step.** Do not re-execute completed (`[x]`) or skipped (`[SKIP]`) steps. Do not assume that a `[>]` step is complete — verify against the step's exit criteria before marking it `[x]`.

## Cold-Start Design Requirement

Each step's **Context** field must be sufficient for cold-start resumption. An agent resuming a plan must be able to execute any step by reading only:
- The plan's header sections (Objective, Constraints, Invariants, Design Decisions)
- The step's own Context, Tasks, Verification, and Exit Criteria fields

Steps must not rely on implicit knowledge accumulated from reading prior steps. This is not just a documentation principle — it is a testable requirement. If a step's Context field omits information that an agent would need to execute it safely, the plan is incomplete.

## State Recovery Examples

**Scenario A — Clean resume**: Progress Log shows Steps 01-03 `[x]`, Step 04 `[ ]`. Resume at Step 04.

**Scenario B — Interrupted step**: Progress Log shows Step 05 `[>]`. Branch `myapp-step-05-auth` exists with 2 commits. Check exit criteria — if not met, continue work on the existing branch. If met but not merged, proceed to strongest-model review and push.

**Scenario C — Branch lost**: Progress Log shows Step 03 `[>]`. No branch found. Treat as `[ ]`, start fresh. Log the restart in the Progress Log Notes.

**Scenario D — Post-skip resume**: Steps 01-04 `[x]`, Step 05 `[SKIP]`, Step 06 `[ ]`. Resume at Step 06. Read the skip reason to understand why Step 05 was bypassed — it may affect Step 06's context.
