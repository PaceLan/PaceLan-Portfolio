import tempfile
import unittest
from pathlib import Path

from application.workspace import ProjectWorkspaceService


class ProjectGoalA2Tests(unittest.TestCase):

    def test_goal_round_trip_through_project_lifecycle(self):
        with tempfile.TemporaryDirectory() as temp:
            project = Path(temp)

            workspace = ProjectWorkspaceService()
            workspace.open_project(project)

            self.assertEqual(workspace.project_goal.text, "")

            workspace.update_project_goal(
                "Build a reliable developer automation assistant"
            )
            self.assertEqual(
                workspace.project_goal.text,
                "Build a reliable developer automation assistant",
            )

            workspace.persist_project()
            workspace.close_project()

            workspace.open_project(project)

            self.assertEqual(
                workspace.project_goal.text,
                "Build a reliable developer automation assistant",
            )

    def test_goal_is_isolated_between_projects(self):
        with tempfile.TemporaryDirectory() as first,              tempfile.TemporaryDirectory() as second:

            first_path = Path(first)
            second_path = Path(second)

            workspace = ProjectWorkspaceService()

            workspace.open_project(first_path)
            workspace.update_project_goal("First project goal")
            workspace.persist_project()
            workspace.close_project()

            workspace.open_project(second_path)

            self.assertEqual(workspace.project_goal.text, "")


if __name__ == "__main__":
    unittest.main()
