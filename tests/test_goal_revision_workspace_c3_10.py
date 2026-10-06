import tempfile
import unittest
from pathlib import Path

from application.draft_input_authority import DraftInputAuthority
from application.goal_confirmation_flow import GoalConfirmationFlow
from application.workspace import ProjectWorkspaceService


class GoalRevisionWorkspaceC310Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name) / "project"
        self.project_path.mkdir()

        self.workspace = ProjectWorkspaceService()
        self.workspace.open_project(self.project_path)

        drafts = DraftInputAuthority()
        flow = GoalConfirmationFlow()

        draft = drafts.accept("Build authentication")
        self.analysis = flow.analyze(
            draft,
            proposed_text="Build secure authentication",
            suggestions=("Add session handling",),
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_revision_does_not_authorize_goal(self):
        revised = self.workspace.revise_goal_analysis(
            self.analysis,
            revised_text="Build secure authentication with sessions",
        )

        self.assertEqual(
            revised.proposed_text,
            "Build secure authentication with sessions",
        )
        self.assertFalse(self.workspace.goal_confirmed)
        self.assertEqual(self.workspace.project_goal.text, "")

    def test_confirmation_after_revision_authorizes_final_goal(self):
        revised = self.workspace.revise_goal_analysis(
            self.analysis,
            revised_text="Build secure authentication with sessions",
        )

        goal = self.workspace.confirm_goal_analysis(revised)

        self.assertEqual(
            goal.text,
            "Build secure authentication with sessions",
        )
        self.assertTrue(self.workspace.goal_confirmed)
        self.assertEqual(
            self.workspace.project_goal.text,
            "Build secure authentication with sessions",
        )

    def test_revision_requires_open_project(self):
        workspace = ProjectWorkspaceService()

        with self.assertRaisesRegex(ValueError, "valid project"):
            workspace.revise_goal_analysis(self.analysis)


if __name__ == "__main__":
    unittest.main()
