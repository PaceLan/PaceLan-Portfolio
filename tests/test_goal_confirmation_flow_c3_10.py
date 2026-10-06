import unittest

from application.draft_input_authority import DraftInputAuthority
from application.goal_confirmation_flow import GoalConfirmationFlow
from application.models import ProjectGoal


class GoalConfirmationFlowC310Tests(unittest.TestCase):
    def setUp(self):
        self.drafts = DraftInputAuthority()
        self.flow = GoalConfirmationFlow()

    def test_draft_analysis_does_not_confirm_goal(self):
        draft = self.drafts.accept(
            "Improve authentication",
            source="external_agent",
        )

        analysis = self.flow.analyze(
            draft,
            proposed_text="Improve authentication security",
        )

        self.assertEqual(
            analysis.proposed_text,
            "Improve authentication security",
        )
        self.assertIsNotNone(analysis.draft)

    def test_analysis_can_contain_suggestions(self):
        draft = self.drafts.accept("Improve authentication")

        analysis = self.flow.analyze(
            draft,
            suggestions=(
                "Clarify security scope",
                "Define verification criteria",
            ),
        )

        self.assertEqual(len(analysis.suggestions), 2)

    def test_confirmation_creates_formal_goal(self):
        draft = self.drafts.accept("Improve authentication")
        analysis = self.flow.analyze(
            draft,
            proposed_text="Improve authentication security",
        )

        confirmation = self.flow.confirm(analysis)

        self.assertIsInstance(confirmation.goal, ProjectGoal)
        self.assertEqual(
            confirmation.goal.text,
            "Improve authentication security",
        )
        self.assertTrue(confirmation.confirmed)

    def test_empty_proposed_goal_is_rejected(self):
        draft = self.drafts.accept("Improve authentication")

        with self.assertRaises(ValueError):
            self.flow.analyze(draft, proposed_text=" ")


if __name__ == "__main__":
    unittest.main()
