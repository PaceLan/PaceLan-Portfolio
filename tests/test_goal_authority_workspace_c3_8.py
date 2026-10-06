import tempfile
import unittest
from pathlib import Path

from application.models import ProjectGoal
from application.workspace import ProjectWorkspaceService


class GoalAuthorityWorkspaceC38Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name) / "project"
        self.project_path.mkdir()

        self.workspace = ProjectWorkspaceService()
        self.workspace.open_project(self.project_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_submit_requires_confirmed_goal(self):
        task = self.workspace.create_task("Implement feature")

        with self.assertRaisesRegex(ValueError, "confirmed project goal"):
            self.workspace.submit_task(task.task_id)

    def test_start_requires_confirmed_goal(self):
        task = self.workspace.create_task("Implement feature")

        with self.assertRaisesRegex(ValueError, "confirmed project goal"):
            self.workspace.start_task(task.task_id)

    def test_confirmed_goal_allows_submit(self):
        self.workspace.update_project_goal("Build feature")
        self.workspace.confirm_project_goal()
        task = self.workspace.create_task("Implement feature")

        submitted = self.workspace.submit_task(task.task_id)

        self.assertEqual(submitted.status.value, "submitted")

    def test_confirmed_goal_allows_start_after_submit(self):
        self.workspace.update_project_goal("Build feature")
        self.workspace.confirm_project_goal()
        task = self.workspace.create_task("Implement feature")

        self.workspace.submit_task(task.task_id)
        started = self.workspace.start_task(task.task_id)

        self.assertEqual(started.status.value, "in_progress")

    def test_goal_change_revokes_confirmation(self):
        self.workspace.update_project_goal("First goal")
        self.workspace.confirm_project_goal()
        self.assertTrue(self.workspace.goal_confirmed)

        self.workspace.update_project_goal("Second goal")

        self.assertFalse(self.workspace.goal_confirmed)

        task = self.workspace.create_task("Implement feature")
        with self.assertRaisesRegex(ValueError, "confirmed project goal"):
            self.workspace.submit_task(task.task_id)

    def test_create_task_remains_draft_entry(self):
        task = self.workspace.create_task("Draft task")

        self.assertEqual(task.status.value, "draft")

    def test_close_project_clears_goal_authority(self):
        self.workspace.update_project_goal("Build feature")
        self.workspace.confirm_project_goal()
        self.assertTrue(self.workspace.goal_confirmed)

        self.workspace.close_project()

        self.assertFalse(self.workspace.goal_confirmed)
        self.assertIsNone(self.workspace.project_goal)


if __name__ == "__main__":
    unittest.main()
