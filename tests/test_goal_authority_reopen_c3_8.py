import tempfile
import unittest
from pathlib import Path

from application.workspace import ProjectWorkspaceService


class GoalAuthorityReopenC38Tests(unittest.TestCase):
    def test_reopen_restores_goal_but_not_confirmation(self):
        with tempfile.TemporaryDirectory() as temp:
            project_path = Path(temp) / "project"
            project_path.mkdir()

            first = ProjectWorkspaceService()
            first.open_project(project_path)
            first.update_project_goal("Build PacePilot")
            first.confirm_project_goal()
            first.persist_project()

            second = ProjectWorkspaceService()
            second.open_project(project_path)

            self.assertEqual(
                second.project_goal.text,
                "Build PacePilot",
            )
            self.assertFalse(second.goal_confirmed)

            with self.assertRaisesRegex(
                ValueError,
                "confirmed project goal",
            ):
                task = second.create_task("Continue work")
                second.submit_task(task.task_id)


if __name__ == "__main__":
    unittest.main()
