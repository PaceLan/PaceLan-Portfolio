from __future__ import annotations

from dataclasses import dataclass

from application.goal_authority import GoalAuthority
from application.models import PlanModel, TaskModel
from application.autonomous_plan_binding import AutonomousPlanBindingService
from application.services import PlanningService
from application.task_management import ProductTask, TaskManagementService


@dataclass(frozen=True)
class AutonomousPlanningRequest:
    project_id: str
    task_id: str


@dataclass(frozen=True)
class AutonomousPlanningResult:
    plan: PlanModel
    task: ProductTask


class AutonomousPlanningService:
    """Create and bind an application Plan for an authorized product Task."""

    def __init__(
        self,
        goal_authority: GoalAuthority,
        planning_service: PlanningService,
        task_management: TaskManagementService,
        plan_binding: AutonomousPlanBindingService | None = None,
    ) -> None:
        self._goal_authority = goal_authority
        self._planning_service = planning_service
        self._task_management = task_management
        self._plan_binding = plan_binding

    def create_from_task(
        self,
        request: AutonomousPlanningRequest,
    ) -> AutonomousPlanningResult:
        goal = self._goal_authority.require_confirmed()

        if not isinstance(request.project_id, str) or not request.project_id:
            raise ValueError("project_id must be a non-empty string")

        if not isinstance(request.task_id, str) or not request.task_id:
            raise ValueError("task_id must be a non-empty string")

        task = self._task_management.get(request.task_id)

        if task.project_id != request.project_id:
            raise ValueError("task does not belong to the requested project")

        description = task.description.strip() or goal.text.strip()
        if not description:
            raise ValueError("task description and confirmed goal cannot both be empty")

        application_task = TaskModel(
            task_id=task.task_id,
            project_id=task.project_id,
            description=description,
        )

        workflow_plan = self._planning_service.build_workflow_plan(
            application_task
        )
        plan = self._planning_service._to_model(workflow_plan)

        if plan.task_id != task.task_id:
            raise ValueError("planning service returned a plan for a different task")

        if plan.project_id != task.project_id:
            raise ValueError("planning service returned a plan for a different project")

        if self._plan_binding is not None:
            self._plan_binding.bind(plan, workflow_plan)

        updated_task = self._task_management.attach_plan(
            task.task_id,
            plan.task_id,
        )

        return AutonomousPlanningResult(
            plan=plan,
            task=updated_task,
        )


__all__ = [
    "AutonomousPlanningRequest",
    "AutonomousPlanningResult",
    "AutonomousPlanningService",
]
