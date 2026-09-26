# Docs Reorganization — Construction Plan

plan-format: 1

## Objective
Reorganize the scattered documentation files in the `webstack` project into a structured `docs/` hierarchy with an auto-generated sidebar navigation file, so that contributors can find and maintain docs without guessing where files belong.

## Constraints
- Sub-agents: read project CLAUDE.md before starting work
- Model tiers — each step's `**Agent**:` field specifies the required model tier. Map to your provider's models:
  - `strongest` = most capable model available (e.g., Opus). Use for architecture, review, risk assessment.
  - `default` = standard model (e.g., Sonnet). Use for implementation, testing, standard tasks.
  - When spawning sub-agents, select the model matching this tier (e.g., in Claude Code: `model: "opus"` for strongest, `model: "sonnet"` or omit for default).
- Preserve all existing content verbatim — this is a reorganization, not a rewrite
- Do not rename files that are linked from external sources (README.md badge URLs, blog posts). Maintain redirects where necessary.
- Complete within a single session if possible; the project has a docs deployment that reads from `docs/`

## Prerequisites
- [ ] Working directory is the `webstack` project root
- [ ] Node.js 20+ installed (required for the sidebar generator script)
- [ ] No other contributor is actively editing docs (check with team lead)

## Design Decisions
1. **Three-tier hierarchy**: `docs/guides/`, `docs/api/`, `docs/contributing/`. Rationale: matches the three audiences (end users, API consumers, contributors). Deeper nesting adds cognitive overhead without value for a project with ~25 doc files.
2. **Sidebar auto-generation over manual maintenance**: a script reads `docs/` structure and produces `docs/sidebar.json`. Rationale: manual sidebar maintenance is the #1 source of stale navigation in the project — 4 of 12 current sidebar entries point to moved/deleted files.
3. **Kebab-case file naming**: rename `GettingStarted.md` → `getting-started.md`, etc. Rationale: consistent with project's existing code file naming convention and avoids case-sensitivity issues across OS.

## Invariants
- All internal doc links resolve (no broken cross-references)
- `node scripts/build-sidebar.js` exits 0 and produces valid JSON
- No doc file exists outside `docs/` after completion (except root `README.md`)

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

### Step 01: Create directory structure and move files [ ]

**Size**: M
**Agent**: default

**Context** (cold-start brief):
The `webstack` project has ~25 markdown doc files scattered across `docs/`, `guides/`, `wiki/`, and the project root. Several naming conventions coexist (PascalCase, kebab-case, spaces). The goal is to consolidate everything under `docs/` with three subdirectories (`guides/`, `api/`, `contributing/`) and normalize all filenames to kebab-case. See Design Decisions for the rationale behind the three-tier hierarchy and naming convention.

**Tasks**:
1. [exact] Create directories: `mkdir -p docs/guides docs/api docs/contributing`
2. [guided] Audit every `.md` file outside `docs/` (excluding root `README.md`). For each file, determine the correct target subdirectory based on content:
   - User-facing tutorials and walkthroughs → `docs/guides/`
   - API reference, endpoint docs, SDK docs → `docs/api/`
   - CONTRIBUTING.md, CODE_OF_CONDUCT.md, dev setup guides → `docs/contributing/`
3. [guided] Move each file to its target, renaming to kebab-case: `mv wiki/GettingStarted.md docs/guides/getting-started.md`
4. [guided] Update all internal cross-references in moved files. Search for relative links (`](../`, `](./`) and absolute links (`](/wiki/`, `](/guides/`) and fix paths to reflect new locations.
5. [exact] Remove empty source directories: `rmdir wiki guides 2>/dev/null || true` (only removes if empty)

**Rollback**: `git checkout -- .` to restore all files to pre-move state (no commits yet at this point).

**Verification**:
- [ ] Automated: `find . -name '*.md' -not -path './node_modules/*' -not -path './docs/*' -not -name 'README.md' | wc -l` returns 0 (no stray docs outside `docs/`)
- [ ] Manual: `grep -r '\[.*\](.*\.md)' docs/ | grep -v node_modules` — inspect output to confirm all relative links point to files that exist under `docs/`

**Exit criteria**: All `.md` files (except root `README.md`) reside under `docs/` in the correct subdirectory with kebab-case names. All internal cross-references updated to reflect new paths.

---

### Step 02: Build sidebar generator script [ ]

**Size**: S
**Agent**: default

**Context** (cold-start brief):
The `webstack` project now has all docs organized under `docs/` with three subdirectories (`guides/`, `api/`, `contributing/`). The project needs an auto-generated `docs/sidebar.json` that reflects this structure, replacing the previously manual sidebar that had 4 stale entries. Node.js 20+ is available. See Design Decision #2 for why auto-generation was chosen over manual maintenance.

**Tasks**:
1. [guided] Create `scripts/build-sidebar.js` that:
   - Reads `docs/` directory recursively
   - For each subdirectory, creates a sidebar group with the directory name as label (title-cased)
   - For each `.md` file, extracts the first `# heading` as the display title (falls back to filename if no heading)
   - Sorts entries alphabetically within each group
   - Writes `docs/sidebar.json` with structure: `[{ "group": "Guides", "items": [{ "title": "...", "path": "..." }] }]`
2. [exact] Add script to `package.json` scripts: `"build:sidebar": "node scripts/build-sidebar.js"`
3. [exact] Run `node scripts/build-sidebar.js` and verify output is valid JSON: `node -e "JSON.parse(require('fs').readFileSync('docs/sidebar.json', 'utf8')); console.log('valid')"`

**Rollback**: Delete `scripts/build-sidebar.js` and `docs/sidebar.json`. Remove the `build:sidebar` script entry from `package.json`.

**Verification**:
- [ ] Automated: `node scripts/build-sidebar.js && node -e "const s = JSON.parse(require('fs').readFileSync('docs/sidebar.json','utf8')); console.log(s.length + ' groups, ' + s.reduce((a,g) => a+g.items.length, 0) + ' items')"` — outputs 3 groups with total item count matching the number of `.md` files under `docs/`
- [ ] Manual: Open `docs/sidebar.json` and verify each entry's `path` points to an existing file

**Exit criteria**: `node scripts/build-sidebar.js` exits 0. `docs/sidebar.json` contains exactly 3 groups. Every `path` value in the JSON points to an existing `.md` file. The `build:sidebar` script is registered in `package.json`.

---

### Step 03: Add link validation and integrate into build [ ]

**Size**: S
**Agent**: default

**Context** (cold-start brief):
The `webstack` project's docs are now organized under `docs/` with auto-generated `docs/sidebar.json` (via `scripts/build-sidebar.js`). The final step adds a link validator to catch broken cross-references early, and wires both the sidebar generator and link validator into the existing build pipeline. The Invariant requires all internal doc links to resolve.

**Tasks**:
1. [guided] Create `scripts/validate-doc-links.js` that:
   - Reads all `.md` files under `docs/`
   - Extracts all markdown links `[text](path)` where path is a relative `.md` reference
   - Resolves each path relative to the file containing the link
   - Reports any links pointing to non-existent files
   - Exits with code 1 if any broken links found, code 0 if all valid
2. [exact] Add script to `package.json` scripts: `"validate:docs": "node scripts/validate-doc-links.js"`
3. [exact] Add to the existing `build` script in `package.json` (append): `&& npm run build:sidebar && npm run validate:docs`
4. [exact] Run the full build to verify integration: `npm run build`

**Rollback**: Remove `scripts/validate-doc-links.js`. Remove `validate:docs` from `package.json` scripts. Revert the `build` script to its original value.

**Verification**:
- [ ] Automated: `npm run validate:docs` exits 0 (no broken links)
- [ ] Automated: `npm run build` exits 0 (sidebar generation + link validation integrated into build)
- [ ] Manual: Intentionally break a link in one doc file, run `npm run validate:docs`, confirm it exits 1 with a clear error message. Then revert the intentional break.

**Exit criteria**: `npm run validate:docs` exits 0 with no broken links reported. `npm run build` includes sidebar generation and link validation. Intentionally breaking a link causes `validate:docs` to fail with a descriptive error.

---

## Dependency Graph

```
Step 01 (move files)
  └──→ Step 02 (sidebar generator)
         └──→ Step 03 (link validation + build integration)
```

**Parallelizable**: None — each step depends on the output of the previous step. Step 02 needs the final directory structure from Step 01. Step 03 validates links produced by Step 01 and integrates the sidebar script from Step 02.

## Progress Log

This table is the single source of truth for execution state.

| Step | Status | Notes |
|------|--------|-------|
| 01   | [ ]    | —     |
| 02   | [ ]    | —     |
| 03   | [ ]    | —     |

## Review Log

- **2026-03-10**: Strongest — Reviewed 3-step plan. Finding 1 (important): Step 01 Tasks item 5 used `rm -rf` for removing source directories — changed to `rmdir` which only removes empty directories, preventing accidental data loss. Finding 2 (minor): Step 02 sidebar script lacked a sort order specification — added "sorts entries alphabetically within each group" to the task description. No critical findings.

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
