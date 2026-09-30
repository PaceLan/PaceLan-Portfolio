import unittest
from unittest.mock import Mock

from application.models import (
    ApplicationExecutionModel,
    PlanModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    StepModel,
    TaskModel,
)
from ui.agent_state import AgentInteractionState
from ui.controller import ApplicationController


class FakeApplicationExecutionService:
    def __init__(self, execution):
        self.execution = execution
        self.received_task = None
        self.received_steps = None

    def run(self, task, steps=()):
        self.received_task = task
        self.received_steps = steps
        return self.execution


class M216AgentWorkflowIntegrationTests(unittest.TestCase):

    def make_execution(self):
        task = TaskModel(
            task_id="task-001",
            project_id="project-001",
            description="Fix authentication",
        )

        plan = PlanModel(
            task_id="task-001",
            project_id="project-001",
            steps=(
                StepModel(
                    step_id="step-001",
                    operation="Inspect authentication",
                ),
            ),
        )

        run = RunModel(
            run_id="run-001",
            task_id="task-001",
        )

        result = ResultModel(
            run_id="run-001",
            status="Success",
            total_steps=1,
            successful_steps=1,
            completed_successfully=True,
        )

        snapshot = SnapshotModel(
            run_id="run-001",
            task_id="task-001",
            run_status="Success",
        )

        return ApplicationExecutionModel(
            task=task,
            plan=plan,
            run=run,
            result=result,
            snapshot=snapshot,
        )

    def make_controller(self):
        controller = ApplicationController()
        controller.application_execution_service = (
            FakeApplicationExecutionService(
                self.make_execution()
            )
        )
        return controller

    def test_controller_accepts_application_execution_boundary(self):
        controller = self.make_controller()

        self.assertIsNotNone(
            controller.application_execution_service,
        )

    def test_controller_runs_agent_through_application_boundary(self):
        controller = self.make_controller()

        task = Mock()
        task.task_id = "task-001"
        task.project_id = "project-001"
        task.description = "Fix authentication"
        task.context = ""

        state = controller.run_agent_task(task, ())

        service = controller.application_execution_service

        self.assertEqual(
            service.received_task.task_id,
            "task-001",
        )
        self.assertEqual(
            service.received_steps,
            (),
        )
        self.assertIsInstance(
            state,
            AgentInteractionState,
        )

    def test_controller_exposes_adapted_agent_state(self):
        controller = self.make_controller()

        task = Mock()
        task.task_id = "task-001"
        task.project_id = "project-001"
        task.description = "Fix authentication"
        task.context = ""

        state = controller.run_agent_task(task)

        self.assertEqual(
            state.task.title,
            "Fix authentication",
        )
        self.assertEqual(
            state.task.description,
            "Fix authentication",
        )
        self.assertEqual(
            state.plan.steps,
            ("Inspect authentication",),
        )
        self.assertEqual(
            state.result.status,
            "Success",
        )

        self.assertIs(
            controller.agent_state,
            state,
        )

    def test_controller_rejects_agent_execution_without_service(self):
        controller = ApplicationController()

        with self.assertRaises(RuntimeError):
            controller.run_agent_task(
                Mock(
                    task_id="task-001",
                    project_id="project-001",
                    description="Test",
                    context="",
                )
            )


if __name__ == "__main__":
    unittest.main()
