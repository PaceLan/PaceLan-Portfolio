import tempfile
import unittest
from pathlib import Path

from application.draft_input_authority import DraftInputAuthority
from application.goal_confirmation_flow import GoalConfirmationFlow
from application.workspace import ProjectWorkspaceService


class GoalConfirmationWorkspaceC310Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.temp_dir.name) / "project"
        self.project_path.mkdir()

        self.workspace = ProjectWorkspaceService()
        self.workspace.open_project(self.project_path)

        self.drafts = DraftInputAuthority()
        self.flow = GoalConfirmationFlow()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_analysis_does_not_confirm_goal(self):
        draft = self.drafts.accept("Build authentication")
        analysis = self.flow.analyze(draft)

        self.assertFalse(self.workspace.goal_confirmed)

    def test_confirmed_analysis_becomes_authorized_goal(self):
        draft = self.drafts.accept("Build authentication")
        analysis = self.flow.analyze(
            draft,
            proposed_text="Build secure authentication",
        )

        goal = self.workspace.confirm_goal_analysis(analysis)

        self.assertEqual(goal.text, "Build secure authentication")
        self.assertEqual(
            self.workspace.project_goal.text,
            "Build secure authentication",
        )
        self.assertTrue(self.workspace.goal_confirmed)

    def test_confirmed_analysis_allows_formal_task_submission(self):
        draft = self.drafts.accept("Build authentication")
        analysis = self.flow.analyze(draft)

        self.workspace.confirm_goal_analysis(analysis)
        task = self.workspace.create_task("Implement authentication")

        submitted = self.workspace.submit_task(task.task_id)

        self.assertEqual(submitted.status.value, "submitted")

    def test_confirmation_requires_open_project(self):
        workspace = ProjectWorkspaceService()
        draft = self.drafts.accept("Build authentication")
        analysis = self.flow.analyze(draft)

        with self.assertRaisesRegex(ValueError, "valid project"):
            workspace.confirm_goal_analysis(analysis)


if __name__ == "__main__":
    unittest.main()
