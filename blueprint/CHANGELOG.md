# Changelog

## 1.0.0 — 2026-03-10

### Added

- Progressive disclosure file structure: main skill file (≤300 lines) with dedicated subdirectories for templates, references, workflows, and examples
- Graceful degradation: memory system, strongest model (e.g., Opus), GitHub CLI, and default branch all degrade gracefully when unavailable
- Anti-pattern catalog: 11 planning anti-patterns with fixes and 6 rationalization rebuttals
- Plan mutation protocol: formal rules for splitting, inserting, skipping, reordering, and abandoning plan steps mid-execution
- Execution resumption protocol: 5-step procedure for resuming partially-executed plans in new sessions
- Two validated example plans: 3-step direct workflow and 9-step branch workflow with step split and parallel groups
- Decision flow DOT digraph for visual routing
- Prescription calibration: zero/low/high freedom tiers for plan content
- 15-item review checklist including anti-pattern scan, verification command validity, and self-consistency analysis
- Agent autonomy boundary: explicit classification of autonomous vs user-confirmed operations
