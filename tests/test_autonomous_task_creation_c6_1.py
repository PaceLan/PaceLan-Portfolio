import tempfile
import unittest
from pathlib import Path

from application.autonomous_task_creation import (
    AutonomousTaskCreationService,
    AutonomousTaskRequest,
)
from application.goal_authority import GoalAuthority
from application.models import ProjectGoal
from application.task_management import TaskManagementService, TaskStatus
from application.workspace import ProjectWorkspaceService


class AutonomousTaskCreationC61Tests(unittest.TestCase):
    def setUp(self):
        self.authority = GoalAuthority()
        self.tasks = TaskManagementService()
        self.service = AutonomousTaskCreationService(
            self.authority,
            self.tasks,
        )

    def test_confirmed_goal_creates_formal_task(self):
        self.authority.set_goal(ProjectGoal(text="Build PacePilot"))
        self.authority.confirm()

        task = self.service.create_from_goal(
            AutonomousTaskRequest(
                project_id="project-c61",
                title="Implement autonomous task creation",
            )
        )

        self.assertEqual(task.project_id, "project-c61")
        self.assertEqual(
            task.title,
            "Implement autonomous task creation",
        )
        self.assertEqual(task.description, "Build PacePilot")
        self.assertEqual(task.status, TaskStatus.DRAFT)

    def test_unconfirmed_goal_is_rejected(self):
        self.authority.set_goal(ProjectGoal(text="Build PacePilot"))

        with self.assertRaisesRegex(
            ValueError,
            "confirmed project goal",
        ):
            self.service.create_from_goal(
                AutonomousTaskRequest(
                    project_id="project-c61",
                    title="Blocked task",
                )
            )

    def test_missing_goal_is_rejected(self):
        with self.assertRaisesRegex(
            ValueError,
            "confirmed project goal",
        ):
            self.service.create_from_goal(
                AutonomousTaskRequest(
                    project_id="project-c61",
                    title="Blocked task",
                )
            )

    def test_explicit_description_overrides_goal_text(self):
        self.authority.set_goal(ProjectGoal(text="Build PacePilot"))
        self.authority.confirm()

        task = self.service.create_from_goal(
            AutonomousTaskRequest(
                project_id="project-c61",
                title="Task",
                description="Specific implementation work.",
            )
        )

        self.assertEqual(
            task.description,
            "Specific implementation work.",
        )

    def test_created_task_is_registered_in_task_service(self):
        self.authority.set_goal(ProjectGoal(text="Build PacePilot"))
        self.authority.confirm()

        task = self.service.create_from_goal(
            AutonomousTaskRequest(
                project_id="project-c61",
                title="Registered task",
            )
        )

        self.assertEqual(self.tasks.get(task.task_id), task)
        self.assertEqual(
            self.tasks.list_for_project("project-c61"),
            (task,),
        )

    def test_workspace_creates_task_from_confirmed_goal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = ProjectWorkspaceService()
            workspace.open_project(Path(temp_dir))
            workspace.update_project_goal("Build autonomous execution")
            workspace.confirm_project_goal()

            task = workspace.create_task_from_goal(
                "Execute autonomous task"
            )

            self.assertEqual(
                task.project_id,
                workspace.project_model.project_id,
            )
            self.assertEqual(task.title, "Execute autonomous task")
            self.assertEqual(
                task.description,
                "Build autonomous execution",
            )
            self.assertEqual(task.status, TaskStatus.DRAFT)
            self.assertEqual(
                tuple(t.task_id for t in workspace.tasks),
                (task.task_id,),
            )

    def test_workspace_rejects_task_creation_without_confirmed_goal(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = ProjectWorkspaceService()
            workspace.open_project(Path(temp_dir))

            with self.assertRaisesRegex(
                ValueError,
                "confirmed project goal",
            ):
                workspace.create_task_from_goal(
                    "Blocked autonomous task"
                )

    def test_workspace_rejects_task_creation_without_open_project(self):
        workspace = ProjectWorkspaceService()

        with self.assertRaisesRegex(
            ValueError,
            "valid project",
        ):
            workspace.create_task_from_goal(
                "Blocked autonomous task"
            )


if __name__ == "__main__":
    unittest.main()
