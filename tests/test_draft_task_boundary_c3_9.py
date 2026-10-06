import tempfile
import unittest
from pathlib import Path

from application.draft_input_authority import (
    DraftInputAuthority,
    DraftInputKind,
)
from application.workspace import ProjectWorkspaceService


class DraftTaskBoundaryC392Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = ProjectWorkspaceService()
        self.workspace.open_project(Path(self.temp_dir.name))
        self.authority = DraftInputAuthority()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_idea_can_become_only_a_draft_task(self):
        idea = self.authority.accept(
            "Implement authentication",
            kind=DraftInputKind.IDEA,
            source="external_agent",
        )

        task = self.workspace.create_task(
            idea.content,
            description="Derived from external idea.",
        )

        self.assertEqual(task.status.value, "draft")

    def test_draft_does_not_bypass_goal_authority(self):
        draft = self.authority.accept("Implement feature")

        task = self.workspace.create_task(draft.content)

        with self.assertRaisesRegex(ValueError, "confirmed project goal"):
            self.workspace.submit_task(task.task_id)

        with self.assertRaisesRegex(ValueError, "confirmed project goal"):
            self.workspace.start_task(task.task_id)

    def test_draft_boundary_has_no_execution_authority(self):
        draft = self.authority.accept("Run implementation")

        self.assertFalse(
            self.authority.can_enter_formal_execution(draft)
        )
        self.assertTrue(
            self.authority.requires_goal_confirmation(draft)
        )


if __name__ == "__main__":
    unittest.main()
