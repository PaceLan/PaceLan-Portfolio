from __future__ import annotations

from dataclasses import dataclass

from application.autonomous_execution import AutonomousExecutionService
from application.autonomous_planning import (
    AutonomousPlanningRequest,
    AutonomousPlanningResult,
    AutonomousPlanningService,
)
from application.autonomous_task_creation import (
    AutonomousTaskCreationService,
    AutonomousTaskRequest,
)
from application.task_management import ProductTask


@dataclass(frozen=True)
class AutonomousDevelopmentRequest:
    project_id: str
    title: str
    description: str = ""


class AutonomousDevelopmentService:
    """Orchestrate the complete autonomous development application flow."""

    def __init__(
        self,
        task_creation: AutonomousTaskCreationService,
        planning: AutonomousPlanningService,
        execution: AutonomousExecutionService,
    ) -> None:
        self._task_creation = task_creation
        self._planning = planning
        self._execution = execution

    def run(
        self,
        request: AutonomousDevelopmentRequest,
    ):
        task = self._task_creation.create_from_goal(
            AutonomousTaskRequest(
                project_id=request.project_id,
                title=request.title,
                description=request.description,
            )
        )

        planning = self._planning.create_from_task(
            AutonomousPlanningRequest(
                project_id=task.project_id,
                task_id=task.task_id,
            )
        )

        return self._execution.run(
            task,
            planning.plan,
        )

    def start(
        self,
        request: AutonomousDevelopmentRequest,
    ):
        task = self._task_creation.create_from_goal(
            AutonomousTaskRequest(
                project_id=request.project_id,
                title=request.title,
                description=request.description,
            )
        )

        planning = self._planning.create_from_task(
            AutonomousPlanningRequest(
                project_id=task.project_id,
                task_id=task.task_id,
            )
        )

        return self._execution.start(
            task,
            planning.plan,
        )


__all__ = [
    "AutonomousDevelopmentRequest",
    "AutonomousDevelopmentService",
]
