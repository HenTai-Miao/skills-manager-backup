"""Domain types: Task and TaskContext."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Task:
    id: int
    title: str
    project_id: int
    assignee_id: Optional[int]
    status: str  # 'open', 'in_progress', 'blocked', 'done', 'cancelled'
    priority: str  # 'low', 'medium', 'high', 'urgent'
    created_at: datetime
    due_at: Optional[datetime] = None
    blocked_by: list[int] = field(default_factory=list)
    # source tag for OON penalty (in-network = own tasks, OON = watched)
    source: str = "owned"


@dataclass
class TaskContext:
    user_id: int
    owned_project_ids: list[int]
    watched_project_ids: list[int]
    blocked_task_ids: set[int]  # tasks the user has snoozed
    already_shown_today: set[int]
    now: datetime = field(default_factory=datetime.utcnow)
