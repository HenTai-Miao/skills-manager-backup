# Extract Scheduler Into Plugin — Construction Plan

plan-format: 1

## Objective
Extract the hardcoded scheduler module from `taskflow` core into a standalone plugin package (`@taskflow/plugin-scheduler`), enabling third-party scheduling backends while keeping the default behavior unchanged. This unblocks community-contributed schedulers (cron, distributed queue, event-driven) without core modifications.

## Constraints
- Sub-agents: read project CLAUDE.md before starting work
- Model tiers — each step's `**Agent**:` field specifies the required model tier. Map to your provider's models:
  - `strongest` = most capable model available (e.g., Opus). Use for architecture, review, risk assessment.
  - `default` = standard model (e.g., Sonnet). Use for implementation, testing, standard tasks.
  - When spawning sub-agents, select the model matching this tier (e.g., in Claude Code: `model: "opus"` for strongest, `model: "sonnet"` or omit for default).
- Zero runtime regressions: existing users who install `@taskflow/plugin-scheduler` alongside core must get identical scheduling behavior to pre-extraction
- The core package (`@taskflow/core`) must have zero scheduler-specific imports after extraction
- Monorepo structure: `packages/core`, `packages/plugin-scheduler`, using pnpm workspace
- All existing tests must pass at every step — no "we'll fix tests later" deferrals
- TypeScript strict mode, no `any` escape hatches

## Prerequisites
- [ ] `pnpm install` succeeds at monorepo root
- [ ] `pnpm -r test` passes (all 847 tests green)
- [ ] `pnpm -r build` succeeds with zero warnings
- [ ] Current branch is up to date with `main`
- [ ] GitHub CLI authenticated: `gh auth status` passes

## Design Decisions
1. **Plugin interface over abstract class**: Define `SchedulerPlugin` as a TypeScript interface, not an abstract base class. Rationale: interfaces have zero runtime footprint, do not couple the plugin to the core's class hierarchy, and are easier to mock in tests. The core uses duck-typing validation at registration time.
2. **Lazy loading via plugin registry**: The scheduler plugin registers itself through `taskflow`'s existing plugin registry (`registerPlugin()`). Core discovers it at startup, not at import time. Rationale: avoids circular dependency between core and plugin; aligns with the established pattern used by `plugin-logger` and `plugin-metrics`.
3. **Default scheduler bundled as plugin**: The current built-in scheduler becomes `@taskflow/plugin-scheduler` with no behavioral changes. Users who install `@taskflow/core` without the scheduler plugin get a clear error at runtime: "No scheduler plugin registered. Install @taskflow/plugin-scheduler or a compatible alternative." Rationale: explicit > implicit; forcing registration prevents silent fallback to a no-op scheduler that would hide misconfiguration.
4. **Step 05 split into 05a/05b**: During planning review, the strongest-model review identified that the original Step 05 ("Extract scheduler and write plugin tests") was a mega-step touching 18+ files. Split into: 05a (move files + update imports) and 05b (write plugin-specific tests). See Review Log.
5. **Shared test utilities stay in core**: `packages/core/test/helpers/` contains shared test factories and mocks. These remain in core (not duplicated to the plugin) and are imported by plugin tests via workspace path. Rationale: DRY; the helpers are used by 6 other test files in core.

## Invariants
- All CI checks pass: `pnpm -r build && pnpm -r test && pnpm -r lint`
- `packages/core/src/` contains zero imports from `@taskflow/plugin-scheduler`
- `packages/core/package.json` does not list `@taskflow/plugin-scheduler` as a dependency
- TypeScript strict mode: `pnpm -r typecheck` passes with zero errors
- Plugin registry accepts and correctly loads `@taskflow/plugin-scheduler`

## Branch & Merge Workflow

### Branch naming
- Format: `taskflow-step-{NN}-{short-desc}` (kebab-case, e.g., `taskflow-step-03-scheduler-interface`)
- Always branch from latest default branch (detected in Phase 1 pre-flight): `git pull origin main && git checkout -b <branch>`
- One branch per step. Never bundle multiple steps into one branch.

### Pre-push strongest-model review gate
Every branch must pass a strongest-model review before pushing to remote. No exceptions.
1. Executing agent completes all tasks and runs verification locally.
2. Executing agent commits all changes on the feature branch.
3. **Before `git push`**: delegate review to a strongest-model sub-agent. If the executing agent is already the strong model, self-review is acceptable — the gate's purpose is to ensure strongest-model scrutiny, not to require a separate agent. The agent must still perform a structured review against the same criteria.
   - Prompt: "Review all commits on branch `{branch}` against `main`. Check: correctness, edge cases, consistency with existing code, CLAUDE.md compliance, security. Return a structured list of findings (critical / important / minor)."
   - If critical or important findings: fix, commit, re-review. Iterate until clean.
   - Minor findings: fix if trivial, otherwise log in Progress Log.
4. Only after review passes: `git push -u origin <branch>`.

### Post-push CI gate
After push, CI must pass before merge.
1. After push: `gh run list -b <branch> --limit 1` to find the CI run.
2. Wait for CI: `gh run watch <run-id>`. Never proceed while CI is pending.
3. If CI fails: diagnose locally → fix → commit → re-review (strongest-model gate) → push → wait for CI again. Never merge a red branch.
4. After CI is green: `gh pr create --title '{step title}' --body '{summary}'`. Then merge: `gh pr merge --squash --delete-branch`. If `gh pr merge` fails due to branch protection rules (required reviewers, pending PR-specific status checks, merge queue), report the blocker to the user and wait for resolution before proceeding. If pre-flight found no `gh` auth, this step is omitted entirely (plan uses direct workflow).
5. After merge: `git checkout main && git pull origin main`. Verify merge commit.

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

### Step 01: Define scheduler plugin interface [x]

**Branch**: `taskflow-step-01-scheduler-interface`
**Size**: S
**Isolation**: main-tree
**Agent**: strongest

**Context** (cold-start brief):
The `taskflow` project is a TypeScript monorepo (`packages/core`) that has a hardcoded scheduler module at `packages/core/src/scheduler/`. The project uses a plugin registry (`registerPlugin()` in `packages/core/src/plugin-registry.ts`) that currently handles `plugin-logger` and `plugin-metrics`. This step defines the `SchedulerPlugin` interface that the scheduler must implement, following the same pattern as existing plugins. See Design Decision #1 for why interface was chosen over abstract class.

**Tasks**:
1. [guided] Create `packages/core/src/types/scheduler-plugin.ts` with the `SchedulerPlugin` interface. Must include:
   - `name: string` — unique plugin identifier
   - `schedule(task: Task, options: ScheduleOptions): Promise<ScheduleHandle>` — schedule a task
   - `cancel(handle: ScheduleHandle): Promise<void>` — cancel a scheduled task
   - `list(): Promise<ScheduleEntry[]>` — list all scheduled tasks
   - `shutdown(): Promise<void>` — graceful shutdown
2. [guided] Define supporting types (`ScheduleOptions`, `ScheduleHandle`, `ScheduleEntry`) in the same file, based on the existing scheduler module's public API surface.
3. [exact] Export from `packages/core/src/types/index.ts`: add `export * from './scheduler-plugin.js'`
4. [exact] Run: `pnpm -r build && pnpm -r typecheck`

**Rollback**: `git checkout -- packages/core/src/types/`

**Verification**:
- [ ] Automated: `pnpm -r build && pnpm -r typecheck` — zero errors
- [ ] Automated: `pnpm -r test` — all 847 tests pass (no regressions from type additions)
- [ ] Manual: Inspect `packages/core/src/types/scheduler-plugin.ts` — confirm interface methods match the existing scheduler's public API

**Exit criteria**: `SchedulerPlugin` interface is exported from `@taskflow/core`. Build and typecheck pass. All existing tests pass unchanged.

---

### Step 02: Add scheduler slot to plugin registry [x]

**Branch**: `taskflow-step-02-registry-slot`
**Size**: S
**Isolation**: main-tree
**Agent**: default

**Context** (cold-start brief):
The `taskflow` plugin registry (`packages/core/src/plugin-registry.ts`) currently supports `logger` and `metrics` plugin slots. Step 01 added a `SchedulerPlugin` interface to `packages/core/src/types/`. This step adds a `scheduler` slot to the registry so plugins implementing `SchedulerPlugin` can register themselves. The registry uses duck-typing validation (Design Decision #1) — it checks that registered objects implement the required interface methods at registration time.

**Tasks**:
1. [guided] Add `scheduler` slot to the plugin registry's slot map in `packages/core/src/plugin-registry.ts`. Follow the existing pattern used by `logger` and `metrics` slots.
2. [guided] Add validation logic: when a scheduler plugin registers, verify it implements all `SchedulerPlugin` interface methods. Throw a descriptive `PluginValidationError` if any method is missing.
3. [guided] Add `getScheduler(): SchedulerPlugin | undefined` accessor to the registry.
4. [guided] Write tests in `packages/core/test/plugin-registry.test.ts`:
   - Registering a valid scheduler plugin succeeds
   - Registering an object missing required methods throws `PluginValidationError`
   - `getScheduler()` returns `undefined` when no scheduler is registered
   - `getScheduler()` returns the registered plugin after registration

**Rollback**: Revert changes to `plugin-registry.ts` and its test file: `git checkout -- packages/core/src/plugin-registry.ts packages/core/test/plugin-registry.test.ts`

**Verification**:
- [ ] Automated: `pnpm -r build && pnpm -r test` — all tests pass including new registry tests
- [ ] Automated: `pnpm -r typecheck` — zero errors

**Exit criteria**: Plugin registry accepts scheduler plugins, validates their interface, and exposes them via `getScheduler()`. Four new tests pass. All pre-existing tests pass.

---

### Step 03: Create plugin package scaffolding [x]

**Branch**: `taskflow-step-03-plugin-scaffold`
**Size**: S
**Isolation**: main-tree
**Agent**: default

**Context** (cold-start brief):
The `taskflow` monorepo uses pnpm workspaces with packages under `packages/`. Two plugin slots exist in the registry: `logger`, `metrics`, and now `scheduler` (added in Step 02). This step creates the `@taskflow/plugin-scheduler` package directory structure without moving any code yet — just the scaffolding. Follow the existing structure of `packages/plugin-logger/` as the reference template.

**Tasks**:
1. [guided] Create package directory structure:
   ```
   packages/plugin-scheduler/
   ├── package.json
   ├── tsconfig.json
   ├── src/
   │   └── index.ts          (empty placeholder, exports nothing yet)
   └── test/
       └── .gitkeep
   ```
2. [guided] `package.json`: name `@taskflow/plugin-scheduler`, version `0.0.1`, `main`/`types` pointing to `dist/`, peer dependency on `@taskflow/core` (workspace:\*). Model after `packages/plugin-logger/package.json`.
3. [guided] `tsconfig.json`: extend from root `tsconfig.base.json`, match settings from `packages/plugin-logger/tsconfig.json`.
4. [exact] Add `"packages/plugin-scheduler"` to root `pnpm-workspace.yaml` if not auto-discovered.
5. [exact] Run: `pnpm install && pnpm -r build`

**Rollback**: `trash packages/plugin-scheduler` (or `rm -rf` if `trash` is unavailable) and revert `pnpm-workspace.yaml` changes.

**Verification**:
- [ ] Automated: `pnpm -r build` — all packages build including the new one
- [ ] Automated: `ls packages/plugin-scheduler/dist/index.js` — compiled output exists
- [ ] Automated: `pnpm -r test` — all existing tests still pass

**Exit criteria**: `@taskflow/plugin-scheduler` package exists in the workspace, builds successfully, and produces `dist/` output. Monorepo build and test remain green.

---

### Step 04: Redirect core scheduler calls through plugin registry [x]

**Branch**: `taskflow-step-04-redirect-calls`
**Size**: M
**Isolation**: worktree
**Agent**: strongest

**Context** (cold-start brief):
The `taskflow` core currently calls the scheduler directly via `import { Scheduler } from './scheduler/index.js'` in multiple places (`packages/core/src/runner.ts`, `packages/core/src/lifecycle.ts`, `packages/core/src/api/schedule-endpoint.ts`). The plugin registry now has a `scheduler` slot with `getScheduler()` (Step 02). This step replaces all direct scheduler imports with calls to `getScheduler()`, which is the critical bridge step that decouples core from the scheduler implementation. This is the riskiest step — it changes core's runtime behavior path. Worktree isolation ensures the main tree stays clean.

**Tasks**:
1. [guided] Identify all files in `packages/core/src/` that import from `./scheduler/` or `../scheduler/`. Expected: `runner.ts`, `lifecycle.ts`, `api/schedule-endpoint.ts` (verify by searching, do not assume).
2. [guided] In each file, replace the direct import with:
   - Import `getScheduler` from the plugin registry
   - Replace `scheduler.method()` calls with `getScheduler()?.method()` or throw a descriptive error if no scheduler is registered ("No scheduler plugin registered. Install @taskflow/plugin-scheduler or a compatible alternative.")
3. [guided] Update the application bootstrap (`packages/core/src/bootstrap.ts`) to check for a registered scheduler during startup and emit a warning log if none is found (not an error — the app can start without a scheduler, but scheduled tasks will fail).
4. [guided] Update affected test files to register a mock scheduler plugin before tests that exercise scheduling. Use `beforeEach(() => registerPlugin('scheduler', mockScheduler))` pattern.
5. [exact] Run: `pnpm -r build && pnpm -r test && pnpm -r typecheck`

**Rollback**: Discard worktree — `git worktree remove taskflow-step-04-redirect-calls`. Main tree is unaffected.

**Verification**:
- [ ] Automated: `pnpm -r build && pnpm -r test` — all 847+ tests pass
- [ ] Automated: `pnpm -r typecheck` — zero errors
- [ ] Automated: `grep -r "from.*['\"]\.\.*/scheduler" packages/core/src/ | grep -v node_modules | wc -l` — returns 0 (no direct scheduler imports remain in core src)
- [ ] Manual: Start the app without a scheduler plugin registered, confirm the warning log appears and the app does not crash

**Exit criteria**: No file in `packages/core/src/` directly imports from `./scheduler/`. All scheduler calls go through `getScheduler()`. Unregistered scheduler produces a clear error message. All tests pass with mock scheduler registration.

---

### Step 05a: Move scheduler implementation to plugin package [>]

**Branch**: `taskflow-step-05a-move-files`
**Size**: M
**Isolation**: worktree
**Agent**: default

**Context** (cold-start brief):
The `taskflow` core's scheduler implementation lives at `packages/core/src/scheduler/` (files: `index.ts`, `queue.ts`, `cron-parser.ts`, `types.ts`). Step 04 already redirected all core imports to go through the plugin registry instead of directly importing the scheduler. The plugin package scaffolding exists at `packages/plugin-scheduler/` (Step 03). This step moves the implementation files from core to the plugin package and wires them up as a proper plugin that registers itself. This was originally part of a combined "Step 05" but was split because the original touched 18+ files — see Design Decision #4 and Review Log.

**Tasks**:
1. [exact] Move implementation files:
   ```
   mv packages/core/src/scheduler/index.ts packages/plugin-scheduler/src/scheduler.ts
   mv packages/core/src/scheduler/queue.ts packages/plugin-scheduler/src/queue.ts
   mv packages/core/src/scheduler/cron-parser.ts packages/plugin-scheduler/src/cron-parser.ts
   ```
2. [guided] Do NOT move `packages/core/src/scheduler/types.ts` — those types were already extracted to `packages/core/src/types/scheduler-plugin.ts` in Step 01. Delete the duplicated type definitions from the moved files and import from `@taskflow/core` instead.
3. [guided] Create `packages/plugin-scheduler/src/index.ts` as the plugin entry point:
   - Import the scheduler implementation
   - Wrap it in a factory function that returns an object satisfying `SchedulerPlugin` interface
   - Export a `register()` function that calls `registerPlugin('scheduler', factory())`
   - Export the factory function for users who want manual control
4. [guided] Update all import paths in moved files (internal cross-references between `scheduler.ts`, `queue.ts`, `cron-parser.ts`).
5. [exact] Verify `packages/core/src/scheduler/` is empty, then remove: `rmdir packages/core/src/scheduler/`
6. [exact] Run: `pnpm install && pnpm -r build && pnpm -r typecheck`

**Rollback**: Discard worktree — `git worktree remove taskflow-step-05a-move-files`. Main tree is unaffected.

**Verification**:
- [ ] Automated: `pnpm -r build` — all packages build including `@taskflow/plugin-scheduler`
- [ ] Automated: `pnpm -r typecheck` — zero errors
- [ ] Automated: `test -d packages/core/src/scheduler && echo "FAIL: scheduler dir still exists" || echo "PASS"` — outputs PASS
- [ ] Automated: `grep -r "from.*['\"]@taskflow/core" packages/plugin-scheduler/src/ | head -5` — confirms plugin imports types from core (not local copies)

**Exit criteria**: `packages/core/src/scheduler/` no longer exists. All scheduler implementation code lives in `packages/plugin-scheduler/src/`. The plugin package builds and type-checks. The plugin imports its interface types from `@taskflow/core`.

---

### Step 05b: Write plugin-specific tests [ ]

**Branch**: `taskflow-step-05b-plugin-tests`
**Size**: M
**Isolation**: worktree
**Agent**: default

**Context** (cold-start brief):
The scheduler implementation has been moved from `packages/core/src/scheduler/` to `packages/plugin-scheduler/src/` (Step 05a). The plugin registers itself via `registerPlugin('scheduler', ...)`. The existing scheduler tests in `packages/core/test/scheduler/` tested the implementation directly — they need to be migrated to the plugin package and adapted to test through the plugin interface. Shared test utilities in `packages/core/test/helpers/` are reused via workspace import (Design Decision #5).

**Tasks**:
1. [guided] Move test files from `packages/core/test/scheduler/` to `packages/plugin-scheduler/test/`:
   - `scheduler.test.ts` → `plugin-scheduler.test.ts` (rename to reflect plugin context)
   - `queue.test.ts` → `queue.test.ts`
   - `cron-parser.test.ts` → `cron-parser.test.ts`
2. [guided] Update test imports: replace `import { Scheduler } from '../../src/scheduler/index.js'` with imports from the plugin's `src/` directory.
3. [guided] Add integration test: register the plugin via `register()`, then verify `getScheduler()` returns a working scheduler that can schedule, list, and cancel tasks.
4. [guided] Import shared test helpers from `packages/core/test/helpers/` using workspace path: `import { createMockTask } from '@taskflow/core/test/helpers/mock-task.js'`
5. [exact] Add test script to `packages/plugin-scheduler/package.json`: `"test": "vitest run"`
6. [exact] Remove now-empty `packages/core/test/scheduler/` directory
7. [exact] Run: `pnpm -r test` — all tests pass (core tests minus moved scheduler tests + new plugin tests)

**Rollback**: Discard worktree. If already committed, `git revert HEAD`.

**Verification**:
- [ ] Automated: `pnpm --filter @taskflow/plugin-scheduler test` — all plugin tests pass
- [ ] Automated: `pnpm -r test` — full test suite passes (core + plugin)
- [ ] Automated: `test -d packages/core/test/scheduler && echo "FAIL" || echo "PASS"` — old test dir removed

**Exit criteria**: All scheduler tests live in `packages/plugin-scheduler/test/`. Plugin test suite passes independently. Full monorepo test suite passes. No scheduler test files remain in core.

---

### Step 06: Update integration tests and examples [ ]

**Branch**: `taskflow-step-06-integration`
**Size**: M
**Isolation**: main-tree
**Agent**: default

**Context** (cold-start brief):
The scheduler has been fully extracted from `packages/core/` into `@taskflow/plugin-scheduler` (Steps 01-05b). Core now discovers the scheduler through the plugin registry. Integration tests in `packages/core/test/integration/` and example files in `examples/` likely still import or reference the scheduler directly from core. This step updates all remaining references to use the plugin.

**Tasks**:
1. [guided] Search for any remaining references to the old scheduler path across the entire monorepo:
   - `grep -r "scheduler" packages/core/src/` — should find only type references and registry calls, no implementation
   - `grep -r "from.*scheduler" packages/core/test/` — find tests still importing old paths
   - `grep -r "scheduler" examples/` — find examples referencing old usage
2. [guided] Update integration tests in `packages/core/test/integration/`:
   - Add `import { register } from '@taskflow/plugin-scheduler'` and call `register()` in `beforeAll` setup
   - Remove any direct scheduler imports
3. [guided] Update example files in `examples/`:
   - Add `@taskflow/plugin-scheduler` to example `package.json` dependencies
   - Add `import '@taskflow/plugin-scheduler/register'` (auto-registration import) to example entry points
4. [guided] Update the project README's "Quick Start" section to include the scheduler plugin installation step
5. [exact] Run: `pnpm -r build && pnpm -r test && pnpm -r lint`

**Rollback**: `git checkout -- packages/core/test/ examples/ README.md`

**Verification**:
- [ ] Automated: `pnpm -r test` — all tests pass
- [ ] Automated: `grep -r "from.*['\"]\.\.*/scheduler" packages/core/ | grep -v node_modules | wc -l` — returns 0
- [ ] Automated: `pnpm -r lint` — no lint errors

**Exit criteria**: Zero direct scheduler imports remain anywhere in `packages/core/`. Integration tests use the plugin via registry. Examples demonstrate plugin installation. All CI checks pass.

---

### Step 07: Add "no scheduler" error path and runtime validation [ ]

**Branch**: `taskflow-step-07-no-scheduler-error`
**Size**: S
**Isolation**: main-tree
**Agent**: default

**Context** (cold-start brief):
The scheduler is now a plugin (`@taskflow/plugin-scheduler`). If a user installs `@taskflow/core` without any scheduler plugin, calls to `getScheduler()` return `undefined`. Step 04 added basic null checks, but this step adds comprehensive user-facing error handling and a dedicated test suite for the "no scheduler" path. See Design Decision #3 for the rationale behind explicit errors over silent no-op fallback.

**Tasks**:
1. [guided] Create `packages/core/src/errors/missing-scheduler.ts`:
   - Export `MissingSchedulerError` class extending `TaskflowError`
   - Error message: "No scheduler plugin registered. Install @taskflow/plugin-scheduler or a compatible alternative. See https://taskflow.dev/docs/plugins/scheduler for setup instructions."
2. [guided] Update all `getScheduler()` call sites to throw `MissingSchedulerError` instead of returning `undefined` (change from Step 04's optional chaining to a definitive throw).
3. [guided] Write tests in `packages/core/test/missing-scheduler.test.ts`:
   - Without scheduler registered: calling `runTask()` with a schedule throws `MissingSchedulerError`
   - Without scheduler registered: app starts successfully (scheduler is optional until used)
   - With scheduler registered: `runTask()` with a schedule works normally
4. [exact] Run: `pnpm -r build && pnpm -r test && pnpm -r typecheck`

**Rollback**: Revert the new error file and test file. Restore optional chaining in call sites: `git checkout -- packages/core/src/`

**Verification**:
- [ ] Automated: `pnpm -r build && pnpm -r test` — all tests pass including new error path tests
- [ ] Automated: `pnpm -r typecheck` — zero errors
- [ ] Manual: Remove scheduler plugin registration from an example, run it, confirm `MissingSchedulerError` is thrown with the correct message

**Exit criteria**: Missing scheduler produces `MissingSchedulerError` with actionable installation instructions. App starts without scheduler (no crash). Three new tests pass. All existing tests pass.

---

### Step 08: Write migration guide and update changelog [ ]

**Branch**: `taskflow-step-08-migration-guide`
**Size**: S
**Isolation**: main-tree
**Agent**: default

**Context** (cold-start brief):
The scheduler extraction (Steps 01-07) is complete. Users upgrading from the pre-extraction version need to know: (1) install `@taskflow/plugin-scheduler` as a new dependency, (2) add a registration call in their bootstrap. This step creates a migration guide and updates the changelog. No code changes — documentation only.

**Tasks**:
1. [open] Create `docs/migrations/scheduler-extraction.md` with:
   - "What changed" section (scheduler moved from core to plugin)
   - "Migration steps" with before/after code snippets
   - "FAQ" covering common questions (Can I use a different scheduler? What happens if I forget the plugin?)
2. [open] Update `CHANGELOG.md`: add entry under the next version header describing the breaking change
3. [open] Update `packages/core/README.md`: add note about scheduler now being a separate plugin
4. [open] Update `packages/plugin-scheduler/README.md`: add installation and usage instructions

**Rollback**: `git checkout -- docs/ CHANGELOG.md packages/core/README.md packages/plugin-scheduler/README.md`

**Verification**:
- [ ] Automated: `pnpm -r build` — build still passes (no code changes, but verifies we didn't break anything)
- [ ] Manual: Read `docs/migrations/scheduler-extraction.md` — verify the before/after code snippets are correct and the migration steps are complete
- [ ] Manual: Verify CHANGELOG entry follows the project's existing changelog format

**Exit criteria**: Migration guide exists with complete before/after instructions. CHANGELOG updated. Both README files updated. No broken links in new docs.

---

### Step 09: Final invariant verification and cleanup [ ]

**Branch**: `taskflow-step-09-final-verification`
**Size**: S
**Isolation**: main-tree
**Agent**: strongest

**Context** (cold-start brief):
All extraction steps (01-08) are complete. The scheduler lives in `@taskflow/plugin-scheduler`, core has no scheduler-specific code, documentation is updated. This final step runs a comprehensive verification pass to confirm all invariants hold, cleans up any leftover artifacts, and ensures the monorepo is in a shippable state.

**Tasks**:
1. [exact] Full CI suite: `pnpm -r build && pnpm -r test && pnpm -r lint && pnpm -r typecheck`
2. [exact] Invariant check — no scheduler in core src: `grep -r "scheduler" packages/core/src/ --include='*.ts' | grep -v 'scheduler-plugin' | grep -v 'getScheduler' | grep -v 'MissingScheduler' | grep -v 'registry'` — must return only type imports and registry integration, no implementation code
3. [exact] Invariant check — no core dependency on plugin: `node -e "const pkg = require('./packages/core/package.json'); const deps = {...pkg.dependencies, ...pkg.devDependencies}; if(deps['@taskflow/plugin-scheduler']) { console.error('FAIL: core depends on plugin'); process.exit(1); } console.log('PASS')"`
4. [guided] Search for any remaining TODO/FIXME/HACK comments related to the extraction: `grep -rn "TODO\|FIXME\|HACK" packages/ --include='*.ts' | grep -i "scheduler\|extract\|migrate"`
5. [guided] Verify `pnpm -r pack --dry-run` for both packages — ensure no unexpected files in the publish list
6. [exact] Run: `pnpm -r build && pnpm -r test`

**Rollback**: Revert any cleanup commits: `git revert HEAD`

**Verification**:
- [ ] Automated: `pnpm -r build && pnpm -r test && pnpm -r lint && pnpm -r typecheck` — all pass
- [ ] Automated: Invariant checks from Tasks 2 and 3 — all pass
- [ ] Manual: Review the final diff from `main` — confirm no unintended changes leaked through

**Exit criteria**: All CI checks pass. All invariants verified. No scheduler implementation code in core. Core has no dependency on the plugin package. No extraction-related TODOs remain. Monorepo is ready for version bump and publish.

---

## Dependency Graph

```
Step 01 (interface)
  ├──→ Step 02 (registry slot)
  │      └──→ Step 04 (redirect calls) ──→ Step 05a (move files)
  │                                              └──→ Step 05b (plugin tests)
  │                                                        │
  └──→ Step 03 (package scaffold) ──────────────→ Step 05a │
                                                           │
                                               ┌───────────┘
                                               ▼
                                    Step 06 (integration) ──→ Step 07 (error path)
                                                                     │
                                               ┌─────────────────────┘
                                               ▼
                                    Step 08 (migration guide) ──→ Step 09 (final verify)
```

**Parallelizable**:
- **Group A** (after Step 01): Step 02 and Step 03 can run concurrently — Step 02 modifies `plugin-registry.ts`, Step 03 creates a new `packages/plugin-scheduler/` directory. No shared files.
- **Group B** (after Step 06): Step 07 and Step 08 could theoretically run in parallel (error handling code vs documentation), but Step 07's error class name appears in Step 08's migration guide FAQ. Run serially for consistency.

## Progress Log

This table is the single source of truth for execution state.

| Step | Status | Branch | PR   | Notes |
|------|--------|--------|------|-------|
| 01   | [x]    | `taskflow-step-01-scheduler-interface` | #42  | Merged. Interface based on existing public API surface. |
| 02   | [x]    | `taskflow-step-02-registry-slot`       | #43  | Merged. Added 4 registry tests. |
| 03   | [x]    | `taskflow-step-03-plugin-scaffold`     | #44  | Merged. Followed `plugin-logger` structure. |
| 04   | [x]    | `taskflow-step-04-redirect-calls`      | #45  | Merged. Found 3 files with direct imports (matched expectation). Updated 12 test files with mock scheduler. Strongest-model review caught a missing null check in `lifecycle.ts` — fixed before push. |
| 05a  | [>]    | `taskflow-step-05a-move-files`         | —    | In progress. Files moved, import paths updated. Build passes, typecheck has 2 remaining errors in `cron-parser.ts` import resolution. |
| 05b  | [ ]    | —                                      | —    | Blocked on 05a. |
| 06   | [ ]    | —                                      | —    | — |
| 07   | [ ]    | —                                      | —    | — |
| 08   | [ ]    | —                                      | —    | — |
| 09   | [ ]    | —                                      | —    | — |

## Review Log

- **2026-03-08**: Strongest (plan review) — Finding 1 (critical): Original Step 05 was a mega-step touching 18+ files (move implementation + write tests + update imports). Split into Step 05a (move files, ~10 files) and Step 05b (write tests, ~8 files) per the one-PR-sized heuristic. Finding 2 (important): Step 04 lacked worktree isolation despite being the riskiest step (changes runtime call path in 3+ core files). Added `Isolation: worktree`. Finding 3 (minor): Step 03 Tasks listed `npm` instead of `pnpm` — corrected to match project constraint. All findings fixed.
- **2026-03-09**: Strongest (Step 04 pre-push review) — Finding 1 (important): `lifecycle.ts` used optional chaining (`getScheduler()?.shutdown()`) in the shutdown path, which silently skips cleanup if scheduler is registered but `getScheduler()` returns undefined due to a race condition during shutdown. Changed to explicit null check with warning log. Finding 2 (minor): commit message said "refactor" but this is a behavior change (new runtime path) — suggested `feat(core): route scheduler calls through plugin registry`. Findings fixed, review passed on second iteration.

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
