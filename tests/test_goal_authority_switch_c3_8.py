import tempfile
import unittest
from pathlib import Path

from application.workspace import ProjectWorkspaceService


class GoalAuthorityProjectSwitchC38Tests(unittest.TestCase):
    def test_project_switch_cannot_leak_previous_confirmation(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()

            workspace = ProjectWorkspaceService()

            workspace.open_project(first)
            workspace.update_project_goal("First goal")
            workspace.confirm_project_goal()
            self.assertTrue(workspace.goal_confirmed)

            workspace.open_project(second)

            self.assertFalse(workspace.goal_confirmed)
            self.assertEqual(workspace.project_goal.text, "")


if __name__ == "__main__":
    unittest.main()
