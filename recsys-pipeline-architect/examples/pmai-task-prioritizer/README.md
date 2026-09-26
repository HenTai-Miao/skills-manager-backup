# PMAI Task Prioritizer Example (Python)

A FastAPI service that ranks pending tasks for a user, using the same six-stage pipeline framework as the X For You algorithm but applied to a different domain: project management.

The "for you" pattern is not specific to social media. Any system that asks "of all the things I could show this user/agent right now, which are the most relevant?" can use it. Task queues are an obvious fit.

## What this does

Endpoint: `GET /tasks/next?user_id=42&limit=10`

Returns the top 10 tasks for user 42, ordered by:

- Tasks owned by the user (in-network source)
- Tasks where the user is a watcher or recently active in the project (out-of-network source)
- Multi-action scoring: P(complete_today), P(complete_this_week), P(blocker), P(stale_after_view) combined with weights
- Diversity by project (so the user doesn't get 10 tasks all from one project)
- Standard filters: closed/cancelled, blocked-by-other-task, snoozed, already-shown-this-session

## Files

```
pmai-task-prioritizer/
├── README.md
├── pyproject.toml
├── pipeline/
│   ├── __init__.py
│   ├── interfaces.py        # the six Protocols
│   ├── runner.py            # Pipeline class
│   ├── sources.py
│   ├── hydrators.py
│   ├── filters.py
│   ├── scorers.py
│   ├── selectors.py
│   └── side_effects.py
├── api.py                   # FastAPI app
├── domain.py                # Task and Context types
└── tests/
    └── test_pipeline.py
```

## Install and run

```bash
pip install -e .
uvicorn api:app --reload
```

Then:

```bash
curl 'http://localhost:8000/tasks/next?user_id=42&limit=10'
```

## Why "for you" for tasks

When PMAI generates suggestions, the agent could output hundreds of candidate tasks. Showing them all is noise. Sorting by hardcoded priority is naive — context matters. The same six-stage pipeline that picks 20 articles for a feed can pick 10 tasks for the user's day.

The scorer outputs `P(complete_today)`, `P(complete_this_week)`, `P(this_is_a_blocker)`, etc. Weights tune the product behavior: a Monday morning weight set might emphasize `P(complete_today)` heavily; an end-of-sprint weight set might emphasize `P(this_is_a_blocker)`.

## Attribution

The six-stage pipeline pattern (Source → Hydrator → Filter → Scorer → Selector → SideEffect) is inspired by xAI's open-sourced X For You algorithm (Apache 2.0). This is an independent reimplementation in Python.

Reference: https://github.com/xai-org/x-algorithm

## License

MIT.
