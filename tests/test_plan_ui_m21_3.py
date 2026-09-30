import unittest

from ui.agent_state import AgentInteractionState, AgentPlanState


class M213PlanStateTests(unittest.TestCase):

    def test_plan_state_supports_summary_and_steps(self):
        state = AgentPlanState(
            summary="Implement authentication fix",
            status="Ready",
            steps=("Inspect code", "Apply fix", "Run tests"),
        )

        self.assertEqual(state.summary, "Implement authentication fix")
        self.assertEqual(state.status, "Ready")
        self.assertEqual(
            state.steps,
            ("Inspect code", "Apply fix", "Run tests"),
        )

    def test_default_plan_is_empty(self):
        state = AgentPlanState()

        self.assertEqual(state.summary, "No plan available")
        self.assertEqual(state.status, "No plan")
        self.assertEqual(state.steps, ())

    def test_plan_state_is_immutable(self):
        state = AgentPlanState()

        with self.assertRaises(Exception):
            state.summary = "changed"

    def test_interaction_state_preserves_plan_state(self):
        plan = AgentPlanState(
            summary="Three-step plan",
            status="Ready",
            steps=("Step 1", "Step 2", "Step 3"),
        )

        state = AgentInteractionState(plan=plan)

        self.assertEqual(state.plan, plan)


if __name__ == "__main__":
    unittest.main()
