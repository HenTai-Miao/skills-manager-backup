"""Scorers for task prioritization.

Multi-action prediction: P(complete_today), P(complete_this_week),
P(this_is_a_blocker), P(stale_after_view). Combined via weighted sum.

The ML predictor here is a placeholder using cheap heuristics. Replace
with a real model that learns from your task-completion history.
"""
import math
from datetime import timedelta

from domain import Task, TaskContext
from .interfaces import ScoredItem


PRIORITY_WEIGHT = {
    "urgent": 1.0,
    "high": 0.7,
    "medium": 0.4,
    "low": 0.2,
}


class MultiActionPredictor:
    """Placeholder predictor. Outputs action probabilities into components."""
    name = "multi_action_predictor"

    async def score(self, ctx: TaskContext, items: list[ScoredItem[Task]]) -> None:
        for s in items:
            t = s.item
            priority_signal = PRIORITY_WEIGHT.get(t.priority, 0.3)

            # Freshness of the task
            age_days = (ctx.now - t.created_at).total_seconds() / 86_400
            freshness = math.exp(-age_days / 14)

            # Due-date pressure
            if t.due_at:
                hours_until_due = (t.due_at - ctx.now).total_seconds() / 3600
                if hours_until_due < 0:
                    due_pressure = 1.0  # overdue
                elif hours_until_due < 24:
                    due_pressure = 0.9
                elif hours_until_due < 168:
                    due_pressure = 0.5
                else:
                    due_pressure = 0.2
            else:
                due_pressure = 0.3

            in_progress = 1.0 if t.status == "in_progress" else 0.0

            p_complete_today = _clamp(
                0.4 * due_pressure + 0.3 * in_progress + 0.2 * priority_signal
            )
            p_complete_this_week = _clamp(
                0.5 * priority_signal + 0.3 * freshness + 0.2 * in_progress
            )
            p_blocker = _clamp(0.5 * priority_signal + 0.3 * due_pressure)
            p_stale = _clamp(0.6 * (1 - freshness))

            s.components = {
                "complete_today": p_complete_today,
                "complete_this_week": p_complete_this_week,
                "this_is_a_blocker": p_blocker,
                "stale_after_view": p_stale,
            }


DEFAULT_WEIGHTS = {
    "complete_today": 3.0,
    "complete_this_week": 1.0,
    "this_is_a_blocker": 2.0,
    "stale_after_view": -0.5,
}


class WeightedSumCombiner:
    name = "weighted_sum"

    def __init__(self, weights: dict[str, float] | None = None):
        self.weights = weights or DEFAULT_WEIGHTS

    async def score(self, _ctx: TaskContext, items: list[ScoredItem[Task]]) -> None:
        for s in items:
            s.score = sum(
                self.weights.get(action, 0.0) * prob
                for action, prob in (s.components or {}).items()
            )


class ProjectDiversityScorer:
    """Attenuate score for repeated projects so the daily list doesn't get
    monopolized by one project."""
    name = "project_diversity"

    def __init__(self, decay_per_repeat: float = 0.6):
        self.decay_per_repeat = decay_per_repeat

    async def score(self, _ctx: TaskContext, items: list[ScoredItem[Task]]) -> None:
        sorted_items = sorted(items, key=lambda s: s.score, reverse=True)
        repeats: dict[int, int] = {}
        for s in sorted_items:
            pid = s.item.project_id
            count = repeats.get(pid, 0)
            if count > 0:
                mult = self.decay_per_repeat ** count
                s.score *= mult
                s.components["diversity_penalty"] = mult
            repeats[pid] = count + 1


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, x))
