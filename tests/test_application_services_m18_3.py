import unittest

from agent_workflow.context_understanding import ContextUnderstandingResult
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_plan import WorkflowStep
from agent_workflow.core_interfaces import Project, Task

from application.models import (
    PlanModel,
    ProjectModel,
    TaskModel,
)
from application.services import (
    PlanningService,
    ProjectService,
    TaskService,
)


class FakeProjectContextAgent(ProjectContextAgentInterface):
    def __init__(self):
        scanner = ProjectScanner(".")
        scan_result = scanner.scan()
        context = ProjectContextBuilder().build(scan_result)
        super().__init__(context=context)


class ApplicationServicesM183Tests(unittest.TestCase):

    def test_project_service_create(self):
        result = ProjectService.create("project-001")

        self.assertIsInstance(result, ProjectModel)
        self.assertEqual(result.project_id, "project-001")

    def test_project_service_from_core(self):
        result = ProjectService.from_core(
            Project(project_id="project-001")
        )

        self.assertIsInstance(result, ProjectModel)
        self.assertEqual(result.project_id, "project-001")

    def test_task_service_create(self):
        result = TaskService.create(
            "task-001",
            "project-001",
            description="Build feature",
            context="Application layer",
        )

        self.assertIsInstance(result, TaskModel)
        self.assertEqual(result.task_id, "task-001")
        self.assertEqual(result.project_id, "project-001")
        self.assertEqual(result.description, "Build feature")
        self.assertEqual(result.context, "Application layer")

    def test_task_service_from_core(self):
        result = TaskService.from_core(
            Task(
                task_id="task-001",
                project_id="project-001",
            ),
            description="Build feature",
            context="Application layer",
        )

        self.assertEqual(result.task_id, "task-001")
        self.assertEqual(result.project_id, "project-001")
        self.assertEqual(result.description, "Build feature")
        self.assertEqual(result.context, "Application layer")

    def test_task_service_to_core(self):
        task = TaskModel(
            task_id="task-001",
            project_id="project-001",
            description="Build feature",
            context="Application layer",
        )

        result = TaskService.to_core(task)

        self.assertIsInstance(result, Task)
        self.assertEqual(result.task_id, "task-001")
        self.assertEqual(result.project_id, "project-001")

    def test_task_service_to_workflow_preserves_context(self):
        task = TaskModel(
            task_id="task-001",
            project_id="project-001",
            description="Build feature",
            context="Application layer",
        )

        result = TaskService.to_workflow(task)

        self.assertEqual(result.task_id, "task-001")
        self.assertEqual(result.project_id, "project-001")
        self.assertEqual(result.description, "Build feature")
        self.assertEqual(result.context, "Application layer")

    def test_planning_service_returns_application_model(self):
        service = PlanningService(
            FakeProjectContextAgent()
        )

        task = TaskModel(
            task_id="task-001",
            project_id="project-001",
            description="Build feature",
            context="Application layer",
        )

        result = service.plan(
            task,
            (
                WorkflowStep(
                    operation="inspect",
                    action=lambda: None,
                ),
            ),
        )

        self.assertIsInstance(result, PlanModel)
        self.assertEqual(result.task_id, "task-001")
        self.assertEqual(result.project_id, "project-001")
        self.assertEqual(len(result.steps), 1)
        self.assertEqual(
            result.steps[0].operation,
            "inspect",
        )

    def test_application_plan_does_not_expose_action(self):
        service = PlanningService(
            FakeProjectContextAgent()
        )

        task = TaskModel(
            task_id="task-001",
            project_id="project-001",
        )

        result = service.plan(
            task,
            (
                WorkflowStep(
                    operation="inspect",
                    action=lambda: None,
                ),
            ),
        )

        self.assertFalse(
            hasattr(result.steps[0], "action")
        )

    def test_application_models_are_immutable(self):
        project = ProjectService.create("project-001")

        with self.assertRaises(AttributeError):
            project.project_id = "changed"

    def test_invalid_project_id_rejected(self):
        with self.assertRaises(ValueError):
            ProjectService.create("")

    def test_invalid_task_id_rejected(self):
        with self.assertRaises(ValueError):
            TaskService.create(
                "",
                "project-001",
            )

    def test_invalid_project_id_for_task_rejected(self):
        with self.assertRaises(ValueError):
            TaskService.create(
                "task-001",
                "",
            )


if __name__ == "__main__":
    unittest.main()