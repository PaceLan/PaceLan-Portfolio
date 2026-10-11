from __future__ import annotations

from dataclasses import dataclass

from application.goal_authority import GoalAuthority
from application.task_management import ProductTask, TaskManagementService


@dataclass(frozen=True)
class AutonomousTaskRequest:
    project_id: str
    title: str
    description: str = ""


class AutonomousTaskCreationService:
    """Create a formal product Task from an authorized project Goal."""

    def __init__(
        self,
        goal_authority: GoalAuthority,
        task_management: TaskManagementService,
    ) -> None:
        self._goal_authority = goal_authority
        self._task_management = task_management

    def create_from_goal(
        self,
        request: AutonomousTaskRequest,
    ) -> ProductTask:
        goal = self._goal_authority.require_confirmed()

        if not isinstance(request.project_id, str) or not request.project_id:
            raise ValueError("project_id must be a non-empty string")

        if not isinstance(request.title, str) or not request.title.strip():
            raise ValueError("title must be a non-empty string")

        description = request.description.strip()
        if not description:
            description = goal.text.strip()

        return self._task_management.create(
            request.project_id,
            request.title.strip(),
            description,
        )
