# Plan Mutation Protocol

A plan is a living document. When execution diverges from the original structure, mutate the plan — never abandon it silently or improvise without recording the change.

## Mutation Types

### 1. Split a Step

Use when a step is too large to complete atomically or a sub-problem turns out to be independent.

- Rename the original step: **Step N → Step Na**
- Create the new sub-step: **Step Nb** (continuing the letter series: Nb, Nc, …)
- If a letter-suffixed step itself needs further splitting, append a numeral: **Step 05a → Step 05a1 + Step 05a2**. This avoids collision with the insert namespace.
- Branch names follow the step label: `project-step-05a-desc`, `project-step-05b-desc`
- Update the Dependency Graph to reflect the new nodes and edges
- Log the split in the Progress Log with the reason (e.g., "split: auth and token storage are independent, can parallelize")

### 2. Insert a Step

Use when a necessary step was missed during planning.

- Assign a letter suffix to avoid renumbering all downstream steps: **Step 05a** inserts between Steps 05 and 06
- If the target letter suffix already exists (e.g., 05a was created by a prior split), use the next available letter (05c, 05d, etc.). Check both the Steps section and the Progress Log before assigning a suffix.
- Branch name follows: `project-step-05a-desc`
- The new step **must pass the cold-start test**: its Context field must be readable by an agent that has not seen any prior steps. Do not rely on implicit knowledge from surrounding steps.
- Update the Dependency Graph to wire the new step into the execution order
- Log the insertion in the Progress Log

### 3. Skip a Step

Use when a step is no longer needed or a previous step made it redundant.

- Mark the step `[SKIP]` and add the reason inline: `### Step 05: {title} [SKIP — reason]`
- **Never delete a skipped step.** Skipped steps are historical record. They prevent future agents from re-attempting an approach that was already tried and ruled out.
- Log the skip in the Progress Log

### 4. Reorder Steps

Use when dependency constraints allow a different execution order that reduces risk or enables earlier parallelism.

- Reorder is only valid **if the dependency graph allows it**
- After reordering, re-validate: no step may read the output of a step that now executes after it
- Update the Dependency Graph to reflect the new order
- Log the reorder in the Progress Log

### 5. Abandon the Plan

Use when the objective is no longer valid, the approach is fundamentally flawed, or the project context has changed enough to make the plan unexecutable.

- Mark the plan header: `## Status: ABANDONED — {reason}`
- Log lessons learned in the Review Log: what was tried, why it failed, what a future plan should do differently
- **Do not delete the file.** Abandoned plans are institutional memory.
- If a new plan is needed, create a fresh file — do not reuse or overwrite the abandoned one

### 6. Scope Change

Use when accumulated mutations affect more than 50% of the remaining (uncompleted) steps.

- Assess whether the plan still represents a coherent objective
- If >50% of remaining steps are affected: **ask the user** whether to continue mutating the existing plan or create a new plan
- Creating a new plan is preferred when the objective itself has changed, not just the implementation approach
- If continuing with the existing plan: log the scope change decision in the Review Log

## Mutation Log Format

All mutations are recorded in the Progress Log Notes column and, for significant changes, the Review Log:

```
Progress Log: Step 05 | [SKIP] | branch: — | PR: — | Notes: skipped — redundant after Step 04 auth refactor
Review Log: 2026-03-10: Coordinator — split Step 07 into 07a (schema) and 07b (migration); dependency graph updated
```
