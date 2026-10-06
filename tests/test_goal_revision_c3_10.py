import unittest

from application.draft_input_authority import DraftInputAuthority
from application.goal_confirmation_flow import GoalConfirmationFlow


class GoalRevisionC310Tests(unittest.TestCase):
    def setUp(self):
        self.authority = DraftInputAuthority()
        self.flow = GoalConfirmationFlow()
        self.draft = self.authority.accept("Build authentication")
        self.analysis = self.flow.analyze(
            self.draft,
            proposed_text="Build secure authentication",
            suggestions=("Add session handling",),
        )

    def test_revision_changes_candidate_goal(self):
        revised = self.flow.revise(
            self.analysis,
            revised_text="Build secure authentication with sessions",
        )

        self.assertEqual(
            revised.proposed_text,
            "Build secure authentication with sessions",
        )

    def test_revision_can_accept_suggestions(self):
        revised = self.flow.revise(
            self.analysis,
            accepted_suggestions=("Add session handling",),
        )

        self.assertEqual(
            revised.suggestions,
            ("Add session handling",),
        )

    def test_revision_does_not_confirm_goal(self):
        revised = self.flow.revise(
            self.analysis,
            revised_text="Build secure authentication",
        )

        confirmation = self.flow.confirm(revised)

        self.assertTrue(confirmation.confirmed)
        self.assertEqual(
            confirmation.goal.text,
            "Build secure authentication",
        )

    def test_empty_revised_goal_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "revised goal"):
            self.flow.revise(
                self.analysis,
                revised_text="   ",
            )


if __name__ == "__main__":
    unittest.main()
