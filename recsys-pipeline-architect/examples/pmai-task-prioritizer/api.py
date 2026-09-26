"""FastAPI app exposing GET /tasks/next.

The InMemoryRepo here is a stand-in. Replace with your real persistence layer.
"""
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Query

from domain import Task, TaskContext
from pipeline import Pipeline
from pipeline.sources import OwnedTasksSource, WatchedTasksSource
from pipeline.hydrators import BlockerChainHydrator
from pipeline.filters import (
    TerminalStatusFilter, SnoozedFilter,
    BlockedByOtherTaskFilter, AlreadyShownTodayFilter,
)
from pipeline.scorers import (
    MultiActionPredictor, WeightedSumCombiner, ProjectDiversityScorer,
)
from pipeline.selectors import TopKSelector
from pipeline.side_effects import MarkShownSideEffect


# ---- In-memory repo (replace with your real one) ----
class InMemoryRepo:
    def __init__(self):
        now = datetime.utcnow()
        self.tasks: dict[int, Task] = {
            1: Task(id=1, title="Fix login bug", project_id=100, assignee_id=42,
                    status="in_progress", priority="urgent",
                    created_at=now - timedelta(hours=4),
                    due_at=now + timedelta(hours=12)),
            2: Task(id=2, title="Review PR #341", project_id=100, assignee_id=42,
                    status="open", priority="high",
                    created_at=now - timedelta(days=1)),
            3: Task(id=3, title="Write API docs", project_id=101, assignee_id=42,
                    status="open", priority="medium",
                    created_at=now - timedelta(days=5)),
            4: Task(id=4, title="Stale planning doc", project_id=101, assignee_id=42,
                    status="open", priority="low",
                    created_at=now - timedelta(days=30)),
            5: Task(id=5, title="Triage incoming bugs", project_id=100, assignee_id=42,
                    status="open", priority="high",
                    created_at=now - timedelta(hours=2)),
            6: Task(id=6, title="Watched: cross-team integration", project_id=200,
                    assignee_id=None, status="open", priority="high",
                    created_at=now - timedelta(hours=6)),
        }
        self.shown_log: list[tuple[int, list[int], datetime]] = []

    async def list_tasks(self, project_ids, assignee_id=None,
                         statuses=None, created_after=None):
        result = []
        for t in self.tasks.values():
            if t.project_id not in project_ids: continue
            if assignee_id is not None and t.assignee_id != assignee_id: continue
            if statuses and t.status not in statuses: continue
            if created_after and t.created_at < created_after: continue
            result.append(t)
        return result

    async def get_blocker_chains(self, ids):
        return {}

    async def record_shown(self, user_id, task_ids, at):
        self.shown_log.append((user_id, task_ids, at))


# ---- App wiring ----
repo = InMemoryRepo()
app = FastAPI(title="PMAI Task Prioritizer")


def build_pipeline() -> Pipeline[TaskContext, Task]:
    return Pipeline(
        sources=[
            OwnedTasksSource(repo),
            WatchedTasksSource(repo),
        ],
        hydrators=[
            BlockerChainHydrator(repo),
        ],
        filters=[
            TerminalStatusFilter(),
            SnoozedFilter(),
            BlockedByOtherTaskFilter(),
            AlreadyShownTodayFilter(),
        ],
        scorers=[
            MultiActionPredictor(),
            WeightedSumCombiner(),
            ProjectDiversityScorer(),
        ],
        selector=TopKSelector(),
        side_effects=[
            MarkShownSideEffect(repo),
        ],
    )


async def build_context(user_id: int) -> TaskContext:
    # In real code: look these up from your user profile / project membership tables.
    return TaskContext(
        user_id=user_id,
        owned_project_ids=[100, 101],
        watched_project_ids=[200],
        blocked_task_ids=set(),
        already_shown_today=set(),
    )


@app.get("/tasks/next")
async def tasks_next(
    user_id: int = Query(..., gt=0),
    limit: int = Query(10, gt=0, le=50),
):
    ctx = await build_context(user_id)
    pipe = build_pipeline()
    results = await pipe.run(ctx, limit)

    return {
        "data": [
            {
                "id": r.item.id,
                "title": r.item.title,
                "project_id": r.item.project_id,
                "priority": r.item.priority,
                "status": r.item.status,
                "score": round(r.score, 4),
                "components": {k: round(v, 4) for k, v in r.components.items()},
            }
            for r in results
        ],
        "meta": {"count": len(results)},
    }


@app.get("/health")
async def health():
    return {"ok": True}
