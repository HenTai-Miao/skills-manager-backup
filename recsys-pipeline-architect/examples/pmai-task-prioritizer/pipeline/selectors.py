"""Selector: sort by final score, return top K."""
from domain import Task, TaskContext
from .interfaces import ScoredItem


class TopKSelector:
    name = "top_k"

    def select(self, _ctx: TaskContext, items: list[ScoredItem[Task]], k: int) -> list[ScoredItem[Task]]:
        return sorted(items, key=lambda s: s.score, reverse=True)[:k]
