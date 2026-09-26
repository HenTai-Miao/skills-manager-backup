"""Two sources: owned projects (in-network) and watched projects (out-of-network).

Replace _query_tasks with your real DB query.
"""
from datetime import timedelta

from domain import Task, TaskContext


class OwnedTasksSource:
    name = "owned"

    def __init__(self, repo):
        self.repo = repo

    async def fetch(self, ctx: TaskContext) -> list[Task]:
        if not ctx.owned_project_ids:
            return []
        tasks = await self.repo.list_tasks(
            project_ids=ctx.owned_project_ids,
            assignee_id=ctx.user_id,
            statuses=["open", "in_progress", "blocked"],
        )
        for t in tasks:
            t.source = "owned"
        return tasks


class WatchedTasksSource:
    name = "watched"

    def __init__(self, repo):
        self.repo = repo

    async def fetch(self, ctx: TaskContext) -> list[Task]:
        if not ctx.watched_project_ids:
            return []
        recent_cutoff = ctx.now - timedelta(days=7)
        tasks = await self.repo.list_tasks(
            project_ids=ctx.watched_project_ids,
            assignee_id=None,
            statuses=["open", "in_progress"],
            created_after=recent_cutoff,
        )
        for t in tasks:
            t.source = "watched"
        return tasks
