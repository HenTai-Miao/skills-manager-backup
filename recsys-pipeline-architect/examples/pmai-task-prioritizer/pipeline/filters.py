"""Filters: drop tasks that should not appear in the list."""
from domain import Task, TaskContext


class TerminalStatusFilter:
    name = "terminal_status"

    def keep(self, _ctx: TaskContext, item: Task) -> bool:
        return item.status not in ("done", "cancelled")


class SnoozedFilter:
    name = "snoozed"

    def keep(self, ctx: TaskContext, item: Task) -> bool:
        return item.id not in ctx.blocked_task_ids


class BlockedByOtherTaskFilter:
    """Drop tasks whose blockers are not yet done."""
    name = "blocked_by_other_task"

    def keep(self, _ctx: TaskContext, item: Task) -> bool:
        # If a task is blocked by others, it shouldn't be prioritized for "do next"
        return len(item.blocked_by) == 0


class AlreadyShownTodayFilter:
    name = "already_shown_today"

    def keep(self, ctx: TaskContext, item: Task) -> bool:
        return item.id not in ctx.already_shown_today
