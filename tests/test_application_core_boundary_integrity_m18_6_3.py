import unittest
from pathlib import Path

from application import (
    PlanModel,
    ProjectModel,
    ResultModel,
    SnapshotModel,
    TaskModel,
)
from application.services import (
    PlanningService,
    ProjectService,
    ResultService,
    SnapshotService,
    TaskService,
)
from agent_workflow.core_interfaces import (
    Project,
    Result,
    Task,
)
from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_plan import WorkflowStep


class ApplicationCoreBoundaryIntegrityM1863Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]
        scan_result = ProjectScanner(root).scan()
        context = ProjectContextBuilder().build(scan_result)
        cls.agent = ProjectContextAgentInterface(context)

    def test_project_mapping_does_not_return_core_object(self):
        project = Project(project_id="project-001")

        model = ProjectService.from_core(project)

        self.assertIsInstance(model, ProjectModel)
        self.assertIsNot(model, project)
        self.assertNotIsInstance(model, Project)

    def test_task_mapping_does_not_return_core_object(self):
        task = Task(
            task_id="task-001",
            project_id="project-001",
        )

        model = TaskService.from_core(task)

        self.assertIsInstance(model, TaskModel)
        self.assertIsNot(model, task)
        self.assertNotIsInstance(model, Task)

    def test_task_to_core_preserves_identity(self):
        model = TaskModel(
            task_id="task-001",
            project_id="project-001",
            description="description",
            context="context",
        )

        core = TaskService.to_core(model)

        self.assertIsInstance(core, Task)
        self.assertEqual(core.task_id, "task-001")
        self.assertEqual(core.project_id, "project-001")
        self.assertIsNot(core, model)

    def test_task_to_workflow_preserves_identity(self):
        model = TaskModel(
            task_id="task-001",
            project_id="project-001",
            description="description",
            context="context",
        )

        workflow_task = TaskService.to_workflow(model)

        self.assertEqual(workflow_task.task_id, "task-001")
        self.assertEqual(workflow_task.project_id, "project-001")
        self.assertEqual(workflow_task.description, "description")
        self.assertEqual(workflow_task.context, "context")

    def test_planning_preserves_step_order(self):
        service = PlanningService(self.agent)

        task = TaskModel(
            task_id="task-001",
            project_id="project-001",
        )

        executed = []

        first = WorkflowStep(
            operation="first",
            action=lambda: executed.append("first"),
            target="one",
        )
        second = WorkflowStep(
            operation="second",
            action=lambda: executed.append("second"),
            target="two",
        )

        model = service.plan(task, (first, second))

        self.assertIsInstance(model, PlanModel)
        self.assertEqual(
            [step.operation for step in model.steps],
            ["first", "second"],
        )
        self.assertEqual(
            [step.target for step in model.steps],
            ["one", "two"],
        )
        self.assertEqual(executed, [])

    def test_planning_does_not_execute_actions(self):
        service = PlanningService(self.agent)

        task = TaskModel(
            task_id="task-001",
            project_id="project-001",
        )

        calls = []

        step = WorkflowStep(
            operation="test",
            action=lambda: calls.append("executed"),
        )

        service.plan(task, (step,))

        self.assertEqual(calls, [])

    def test_result_mapping_returns_application_model(self):
        result = Result(
            run_id="run-001",
            status="FAILED",
        )

        model = ResultService.from_core(result)

        self.assertIsInstance(model, ResultModel)
        self.assertIsNot(model, result)
        self.assertNotIsInstance(model, Result)

    def test_result_mapping_preserves_identity_and_status(self):
        result = Result(
            run_id="run-001",
            status="FAILED",
        )

        model = ResultService.from_core(result)

        self.assertEqual(model.run_id, result.run_id)
        self.assertEqual(model.status, result.status)

    def test_snapshot_mapping_returns_application_model(self):
        with self.assertRaises(TypeError):
            SnapshotService.from_core("not-a-snapshot")

    def test_snapshot_mapping_does_not_expose_core_snapshot(self):
        self.assertTrue(
            hasattr(ExecutionSnapshot, "__dataclass_fields__")
            or hasattr(ExecutionSnapshot, "__annotations__")
        )

    def test_application_models_have_no_core_back_reference(self):
        task = Task(
            task_id="task-001",
            project_id="project-001",
        )

        model = TaskService.from_core(task)

        for value in vars(model).values():
            if value is not None:
                self.assertNotEqual(type(value), Task)

    def test_planning_returns_detached_application_steps(self):
        service = PlanningService(self.agent)

        task = TaskModel(
            task_id="task-001",
            project_id="project-001",
        )

        original = WorkflowStep(
            operation="read",
            action=lambda: None,
            target=".",
        )

        model = service.plan(task, (original,))

        self.assertEqual(len(model.steps), 1)
        self.assertIsNot(model.steps[0], original)
        self.assertEqual(model.steps[0].operation, original.operation)
        self.assertEqual(model.steps[0].target, original.target)


if __name__ == "__main__":
    unittest.main()
