import unittest
from pathlib import Path

from application import (
    ExecutionModel,
    PlanModel,
    ProjectModel,
    ResultModel,
    RunModel,
    TaskModel,
)
from application.services import (
    ExecutionService,
    PlanningService,
    ProjectService,
    ResultService,
    RunService,
    SnapshotService,
    TaskService,
)
from agent_workflow.context_understanding import ContextUnderstandingResult
from agent_workflow.core_interfaces import (
    Execution,
    Project,
    Result,
    Run,
    Task,
)
from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_plan import WorkflowStep


class ApplicationServiceContractM1862Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]

        scan_result = ProjectScanner(root).scan()
        context = ProjectContextBuilder().build(scan_result)
        cls.agent = ProjectContextAgentInterface(context)

    def test_project_service_returns_project_model(self):
        project = Project(project_id="project-001")

        model = ProjectService.from_core(project)

        self.assertIsInstance(model, ProjectModel)
        self.assertEqual(model.project_id, "project-001")

    def test_project_service_rejects_invalid_core_input(self):
        with self.assertRaises(TypeError):
            ProjectService.from_core("project-001")

    def test_task_service_returns_task_model(self):
        task = Task(
            task_id="task-001",
            project_id="project-001",
        )

        model = TaskService.from_core(
            task,
            description="Test task",
            context="Test context",
        )

        self.assertIsInstance(model, TaskModel)
        self.assertEqual(model.task_id, "task-001")
        self.assertEqual(model.project_id, "project-001")
        self.assertEqual(model.description, "Test task")
        self.assertEqual(model.context, "Test context")

    def test_task_service_round_trip_preserves_identity(self):
        model = TaskService.create(
            "task-001",
            "project-001",
            description="Test task",
            context="Test context",
        )

        core_task = TaskService.to_core(model)

        self.assertIsInstance(core_task, Task)
        self.assertEqual(core_task.task_id, model.task_id)
        self.assertEqual(core_task.project_id, model.project_id)

    def test_task_service_rejects_invalid_inputs(self):
        with self.assertRaises(TypeError):
            TaskService.to_core("invalid")

        with self.assertRaises(TypeError):
            TaskService.to_workflow("invalid")

    def test_planning_service_returns_plan_model(self):
        service = PlanningService(self.agent)

        task = TaskService.create(
            "task-001",
            "project-001",
            description="Test task",
            context="Test context",
        )

        plan = service.plan(task)

        self.assertIsInstance(plan, PlanModel)
        self.assertEqual(plan.task_id, "task-001")
        self.assertEqual(plan.project_id, "project-001")
        self.assertIsInstance(plan.steps, tuple)

    def test_planning_service_rejects_invalid_task(self):
        service = PlanningService(self.agent)

        with self.assertRaises(TypeError):
            service.plan("invalid")

    def test_planning_service_rejects_invalid_context(self):
        service = PlanningService(self.agent)

        task = TaskService.create(
            "task-001",
            "project-001",
        )

        with self.assertRaises(TypeError):
            service.plan_from_context(
                task,
                "invalid",
            )

    def test_run_service_returns_run_model(self):
        run = Run(
            run_id="run-001",
            task_id="task-001",
        )

        model = RunService.from_core(run)

        self.assertIsInstance(model, RunModel)
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.task_id, "task-001")

    def test_execution_service_returns_execution_model(self):
        execution = Execution(
            run_id="run-001",
            status="SUCCESS",
        )

        model = ExecutionService.from_core(execution)

        self.assertIsInstance(model, ExecutionModel)
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.status, "SUCCESS")

    def test_result_service_returns_result_model(self):
        result = Result(
            run_id="run-001",
            status="FAILED",
        )

        model = ResultService.from_core(result)

        self.assertIsInstance(model, ResultModel)
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.status, "FAILED")

    def test_result_service_rejects_invalid_core_result(self):
        with self.assertRaises(TypeError):
            ResultService.from_core("invalid")

    def test_snapshot_service_rejects_invalid_snapshot(self):
        with self.assertRaises(TypeError):
            SnapshotService.from_core("invalid")

    def test_planning_service_preserves_supplied_step_contract(self):
        service = PlanningService(self.agent)

        task = TaskService.create(
            "task-001",
            "project-001",
        )

        step = WorkflowStep(
            operation="read",
            action=lambda: None,
            target=".",
        )

        plan = service.plan(task, (step,))

        self.assertIsInstance(plan, PlanModel)
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].operation, "read")
        self.assertEqual(plan.steps[0].target, ".")


if __name__ == "__main__":
    unittest.main()
