import unittest

from application.goal_authority import GoalAuthority
from application.models import ProjectGoal


class GoalAuthorityC38Tests(unittest.TestCase):
    def setUp(self):
        self.authority = GoalAuthority()
        self.goal = ProjectGoal(text="Build PacePilot")

    def test_initial_state_is_unconfirmed(self):
        self.assertIsNone(self.authority.goal)
        self.assertFalse(self.authority.confirmed)

    def test_set_goal_does_not_confirm(self):
        self.authority.set_goal(self.goal)

        self.assertEqual(self.authority.goal, self.goal)
        self.assertFalse(self.authority.confirmed)

    def test_confirm_requires_existing_goal(self):
        with self.assertRaisesRegex(ValueError, "goal must exist"):
            self.authority.confirm()

    def test_confirm_marks_goal_authorized(self):
        self.authority.set_goal(self.goal)

        confirmed = self.authority.confirm()

        self.assertEqual(confirmed, self.goal)
        self.assertTrue(self.authority.confirmed)
        self.assertEqual(self.authority.require_confirmed(), self.goal)

    def test_replacing_goal_revokes_confirmation(self):
        self.authority.set_goal(self.goal)
        self.authority.confirm()

        replacement = ProjectGoal(text="Different goal")
        self.authority.set_goal(replacement)

        self.assertEqual(self.authority.goal, replacement)
        self.assertFalse(self.authority.confirmed)
        with self.assertRaisesRegex(ValueError, "confirmed project goal"):
            self.authority.require_confirmed()

    def test_clear_removes_goal_and_confirmation(self):
        self.authority.set_goal(self.goal)
        self.authority.confirm()

        self.authority.clear()

        self.assertIsNone(self.authority.goal)
        self.assertFalse(self.authority.confirmed)

    def test_require_confirmed_rejects_unconfirmed_goal(self):
        self.authority.set_goal(self.goal)

        with self.assertRaisesRegex(ValueError, "confirmed project goal"):
            self.authority.require_confirmed()


if __name__ == "__main__":
    unittest.main()
