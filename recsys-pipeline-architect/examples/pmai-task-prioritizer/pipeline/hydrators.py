"""Hydrators enrich tasks with metadata the sources didn't fetch.

Placeholder: in production, batch-fetch from your DB or service layer.
"""
from domain import Task, TaskContext


class BlockerChainHydrator:
    """Populate task.blocked_by from a relations table."""
    name = "blocker_chain"

    def __init__(self, repo):
        self.repo = repo

    async def hydrate(self, ctx: TaskContext, items: list[Task]) -> None:
        if not items:
            return
        ids = [t.id for t in items]
        chain_map = await self.repo.get_blocker_chains(ids)
        for t in items:
            t.blocked_by = chain_map.get(t.id, [])
