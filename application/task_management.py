from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from uuid import uuid4


class TaskStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class ProductTask:
    task_id: str
    project_id: str
    title: str
    description: str = ""
    plan_id: str | None = None
    status: TaskStatus = TaskStatus.DRAFT

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or not self.task_id:
            raise ValueError("task_id must be a non-empty string")
        if not isinstance(self.project_id, str) or not self.project_id:
            raise ValueError("project_id must be a non-empty string")
        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title must be a non-empty string")


class TaskManagementService:
    """Manage the product-facing Task lifecycle.

    This layer owns task lifecycle state. It does not replace the
    existing application TaskModel or the locked Core Task contract.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, ProductTask] = {}

    def create(
        self,
        project_id: str,
        title: str,
        description: str = "",
        *,
        task_id: str | None = None,
    ) -> ProductTask:
        task = ProductTask(
            task_id=task_id or uuid4().hex,
            project_id=project_id,
            title=title,
            description=description,
        )
        if task.task_id in self._tasks:
            raise ValueError(f"task_id is already registered: {task.task_id}")
        self._tasks[task.task_id] = task
        return task

    def get(self, task_id: str) -> ProductTask:
        try:
            return self._tasks[task_id]
        except KeyError as exc:
            raise KeyError(f"Unknown task_id: {task_id}") from exc

    def list_for_project(self, project_id: str) -> tuple[ProductTask, ...]:
        return tuple(
            task for task in self._tasks.values()
            if task.project_id == project_id
        )

    def attach_plan(self, task_id: str, plan_id: str) -> ProductTask:
        if not isinstance(plan_id, str) or not plan_id:
            raise ValueError("plan_id must be a non-empty string")

        task = self.get(task_id)

        updated = ProductTask(
            task_id=task.task_id,
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            plan_id=plan_id,
            status=task.status,
        )
        self._tasks[task_id] = updated
        return updated

    def submit(self, task_id: str) -> ProductTask:
        return self._transition(task_id, TaskStatus.SUBMITTED, {
            TaskStatus.DRAFT,
        })

    def start(self, task_id: str) -> ProductTask:
        return self._transition(task_id, TaskStatus.IN_PROGRESS, {
            TaskStatus.SUBMITTED,
        })

    def complete(self, task_id: str) -> ProductTask:
        return self._transition(task_id, TaskStatus.COMPLETED, {
            TaskStatus.IN_PROGRESS,
        })

    def fail(self, task_id: str) -> ProductTask:
        return self._transition(task_id, TaskStatus.FAILED, {
            TaskStatus.IN_PROGRESS,
        })

    def block(self, task_id: str) -> ProductTask:
        return self._transition(task_id, TaskStatus.BLOCKED, {
            TaskStatus.SUBMITTED,
            TaskStatus.IN_PROGRESS,
        })

    def cancel(self, task_id: str) -> ProductTask:
        return self._transition(task_id, TaskStatus.CANCELLED, {
            TaskStatus.DRAFT,
            TaskStatus.SUBMITTED,
            TaskStatus.IN_PROGRESS,
            TaskStatus.BLOCKED,
        })

    def _transition(
        self,
        task_id: str,
        target: TaskStatus,
        allowed: set[TaskStatus],
    ) -> ProductTask:
        task = self.get(task_id)
        if task.status not in allowed:
            raise RuntimeError(
                f"invalid task transition from {task.status.value} to {target.value}"
            )

        updated = ProductTask(
            task_id=task.task_id,
            project_id=task.project_id,
            title=task.title,
            description=task.description,
            plan_id=task.plan_id,
            status=target,
        )
        self._tasks[task_id] = updated
        return updated
