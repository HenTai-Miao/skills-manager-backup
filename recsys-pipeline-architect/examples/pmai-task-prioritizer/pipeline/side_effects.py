"""Side effects: record which tasks were shown so we don't show them again today."""
from domain import Task, TaskContext
from .interfaces import ScoredItem


class MarkShownSideEffect:
    name = "mark_shown"

    def __init__(self, repo):
        self.repo = repo

    async def emit(self, ctx: TaskContext, items: list[ScoredItem[Task]]) -> None:
        if not items:
            return
        task_ids = [s.item.id for s in items]
        await self.repo.record_shown(user_id=ctx.user_id, task_ids=task_ids, at=ctx.now)
