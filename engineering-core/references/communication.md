# Communication Standards

## Core Principles

- Keep transient plans, logs, and summaries in chat.
- Do not create unsolicited analysis files.
- For GitHub/GitLab tasks, prefer official forge CLI over browser UI when the CLI can perform the action.
- Use `gh` for GitHub and `glab` for GitLab.
- If a workflow only supports one forge's mechanics, state that limit explicitly. Do not invent unsupported browser or CLI flows.
- Sandbox SSH/Git-over-SSH error `Bad owner or permissions on /etc/ssh/ssh_config.d/...` -> assume sandbox ownership-check issue first.
- Rerun same command outside sandbox before proposing `/etc/ssh` edits, permission fixes, or remote rewrites.
- If error reproduces outside sandbox, treat as real host SSH issue. HTTPS + forge credential helper = fallback, not default.

## Decision-Making

- Use `human-decision-points.md` for escalation triggers.
- Otherwise proceed autonomously with verifiable evidence.
