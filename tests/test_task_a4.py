from pathlib import Path
import tempfile
import unittest

from application.workspace import ProjectWorkspaceService
from application.task_management import (
    ProductTask,
    TaskManagementService,
    TaskStatus,
)


class TestTaskManagementA4(unittest.TestCase):

    def test_create_task(self):
        service = TaskManagementService()

        task = service.create(
            "project-a4",
            "Implement task lifecycle",
            "Build the product Task layer.",
            task_id="task-a4",
        )

        self.assertIsInstance(task, ProductTask)
        self.assertEqual(task.task_id, "task-a4")
        self.assertEqual(task.project_id, "project-a4")
        self.assertEqual(task.title, "Implement task lifecycle")
        self.assertEqual(task.status, TaskStatus.DRAFT)

    def test_task_can_attach_plan(self):
        service = TaskManagementService()
        service.create(
            "project-a4",
            "Plan task",
            task_id="task-a4",
        )

        task = service.attach_plan("task-a4", "plan-a4")

        self.assertEqual(task.plan_id, "plan-a4")
        self.assertEqual(task.status, TaskStatus.DRAFT)

    def test_submit_start_complete_lifecycle(self):
        service = TaskManagementService()
        service.create("project-a4", "Lifecycle", task_id="task-a4")

        self.assertEqual(
            service.submit("task-a4").status,
            TaskStatus.SUBMITTED,
        )
        self.assertEqual(
            service.start("task-a4").status,
            TaskStatus.IN_PROGRESS,
        )
        self.assertEqual(
            service.complete("task-a4").status,
            TaskStatus.COMPLETED,
        )

    def test_failed_and_blocked_states(self):
        service = TaskManagementService()
        service.create("project-a4", "Lifecycle", task_id="task-a4")

        service.submit("task-a4")
        service.start("task-a4")
        self.assertEqual(
            service.fail("task-a4").status,
            TaskStatus.FAILED,
        )

        service.create("project-a4", "Blocked", task_id="task-blocked")
        service.submit("task-blocked")
        self.assertEqual(
            service.block("task-blocked").status,
            TaskStatus.BLOCKED,
        )

    def test_invalid_transition_is_rejected(self):
        service = TaskManagementService()
        service.create("project-a4", "Lifecycle", task_id="task-a4")

        with self.assertRaises(RuntimeError):
            service.start("task-a4")

    def test_workspace_can_attach_task_plan(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir)
            workspace = ProjectWorkspaceService()
            workspace.open_project(project_path)

            task = workspace.create_task("Implement feature")
            updated = workspace.attach_task_plan(task.task_id, "plan-001")

            self.assertEqual(updated.plan_id, "plan-001")
            self.assertEqual(updated.project_id, workspace.project_model.project_id)

    def test_workspace_rejects_task_from_other_project(self):
        with tempfile.TemporaryDirectory() as first_dir, tempfile.TemporaryDirectory() as second_dir:
            first = ProjectWorkspaceService()
            first.open_project(Path(first_dir))
            task = first.create_task("Task")

            second = ProjectWorkspaceService()
            second.open_project(Path(second_dir))

            with self.assertRaises(ValueError):
                second.attach_task_plan(task.task_id, "plan-001")

    def test_workspace_rejects_empty_plan_id(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = ProjectWorkspaceService()
            workspace.open_project(Path(temp_dir))
            task = workspace.create_task("Task")

            with self.assertRaises(ValueError):
                workspace.attach_task_plan(task.task_id, " ")

    def test_tasks_are_isolated_by_project(self):
        service = TaskManagementService()
        service.create("project-a4-a", "Alpha", task_id="task-alpha")
        service.create("project-a4-b", "Beta", task_id="task-beta")

        self.assertEqual(
            tuple(t.task_id for t in service.list_for_project("project-a4-a")),
            ("task-alpha",),
        )

    def test_task_is_exposed_through_project_workspace(self):

        with tempfile.TemporaryDirectory() as temp:
            workspace = ProjectWorkspaceService()
            workspace.open_project(Path(temp))

            task = workspace.create_task(
                "Workspace task",
                "Task created through the project boundary.",
                task_id="workspace-task",
            )

            self.assertEqual(task.project_id, workspace.project_model.project_id)
            self.assertEqual(tuple(t.task_id for t in workspace.tasks), (
                "workspace-task",
            ))
            self.assertEqual(
                workspace.submit_task("workspace-task").status,
                TaskStatus.SUBMITTED,
            )

    def test_unknown_task_is_rejected(self):
        service = TaskManagementService()

        with self.assertRaises(KeyError):
            service.get("missing")


if __name__ == "__main__":
    unittest.main()
