from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class DevelopmentNodeType(str, Enum):
    PROJECT = "project"
    MODULE = "module"
    TASK = "task"
    RUN = "run"
    MILESTONE = "milestone"


class DevelopmentNodeStatus(str, Enum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class DevelopmentTreeNode:
    node_id: str
    project_id: str
    node_key: str
    node_type: DevelopmentNodeType
    status: DevelopmentNodeStatus
    title: str
    parent_id: str | None = None
    started_at: str | None = None
    completed_at: str | None = None
    task_id: str | None = None
    run_id: str | None = None
    history_id: str | None = None
    summary: str = ""

    def __post_init__(self) -> None:
        for name in ("node_id", "project_id", "node_key", "title"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        for name in (
            "parent_id", "started_at", "completed_at",
            "task_id", "run_id", "history_id"
        ):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(f"{name} must be a non-empty string or None")

        if not isinstance(self.node_type, DevelopmentNodeType):
            raise TypeError("node_type must be a DevelopmentNodeType")
        if not isinstance(self.status, DevelopmentNodeStatus):
            raise TypeError("status must be a DevelopmentNodeStatus")
        if not isinstance(self.summary, str):
            raise TypeError("summary must be a string")

        for name in ("started_at", "completed_at"):
            value = getattr(self, name)
            if value is not None:
                try:
                    datetime.fromisoformat(value.replace("Z", "+00:00"))
                except ValueError as exc:
                    raise ValueError(
                        f"{name} must be a valid ISO-8601 timestamp"
                    ) from exc

        if self.node_id == self.parent_id:
            raise ValueError("node cannot be its own parent")

        if self.status == DevelopmentNodeStatus.COMPLETED:
            if self.completed_at is None:
                raise ValueError(
                    "completed_at is required for completed nodes"
                )


__all__ = [
    "DevelopmentNodeStatus",
    "DevelopmentNodeType",
    "DevelopmentTreeNode",
]
