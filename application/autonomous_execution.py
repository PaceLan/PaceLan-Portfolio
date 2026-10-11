from __future__ import annotations

from dataclasses import dataclass

from application.autonomous_plan_binding import AutonomousPlanBindingService
from application.models import ApplicationExecutionModel, PlanModel, TaskModel
from application.services import ApplicationExecutionService
from application.task_management import ProductTask


@dataclass(frozen=True)
class AutonomousExecutionRequest:
    project_id: str
    task_id: str


class AutonomousExecutionService:
    """Application orchestration boundary for autonomous task execution."""

    def __init__(
        self,
        execution_service: ApplicationExecutionService,
        plan_binding: AutonomousPlanBindingService,
    ) -> None:
        if not isinstance(execution_service, ApplicationExecutionService):
            raise TypeError(
                "execution_service must be an ApplicationExecutionService"
            )
        if not isinstance(plan_binding, AutonomousPlanBindingService):
            raise TypeError(
                "plan_binding must be an AutonomousPlanBindingService"
            )

        self._execution_service = execution_service
        self._plan_binding = plan_binding

    @staticmethod
    def _to_application_task(
        task: ProductTask,
        plan: PlanModel,
    ) -> TaskModel:
        if not isinstance(task, ProductTask):
            raise TypeError("task must be a ProductTask")
        if not isinstance(plan, PlanModel):
            raise TypeError("plan must be a PlanModel")

        if task.task_id != plan.task_id:
            raise ValueError(
                "task and plan must have the same task_id"
            )
        if task.project_id != plan.project_id:
            raise ValueError(
                "task and plan must belong to the same project"
            )

        return TaskModel(
            task_id=task.task_id,
            project_id=task.project_id,
            description=task.description,
        )

    def run(
        self,
        task: ProductTask,
        plan: PlanModel,
    ) -> ApplicationExecutionModel:
        application_task = self._to_application_task(task, plan)
        workflow_plan = self._plan_binding.get_for_plan(plan)

        return self._execution_service.run(
            application_task,
            steps=workflow_plan.steps,
        )

    def start(
        self,
        task: ProductTask,
        plan: PlanModel,
    ):
        application_task = self._to_application_task(task, plan)
        workflow_plan = self._plan_binding.get_for_plan(plan)

        return self._execution_service.start(
            application_task,
            steps=workflow_plan.steps,
        )


__all__ = [
    "AutonomousExecutionRequest",
    "AutonomousExecutionService",
]
