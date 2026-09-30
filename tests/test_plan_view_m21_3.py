import unittest
import tkinter as tk

from ui.agent_panel import AgentInteractionPanel
from ui.agent_state import AgentInteractionState, AgentPlanState


class M213PlanViewTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def test_plan_view_displays_summary_and_status(self):
        state = AgentInteractionState(
            plan=AgentPlanState(
                summary="Implement authentication fix",
                status="Ready",
                steps=("Inspect code", "Apply fix", "Run tests"),
            )
        )

        panel = AgentInteractionPanel(self.root, state)

        self.assertEqual(
            panel.plan_summary.cget("text"),
            "Implement authentication fix",
        )
        self.assertEqual(
            panel.plan_status.cget("text"),
            "Ready",
        )

    def test_plan_view_displays_step_count(self):
        state = AgentInteractionState(
            plan=AgentPlanState(
                summary="Three-step plan",
                status="Ready",
                steps=("Step 1", "Step 2", "Step 3"),
            )
        )

        panel = AgentInteractionPanel(self.root, state)

        self.assertEqual(
            panel.plan_step_count.cget("text"),
            "3 steps",
        )

    def test_plan_view_displays_empty_plan(self):
        panel = AgentInteractionPanel(
            self.root,
            AgentInteractionState(),
        )

        self.assertEqual(
            panel.plan_summary.cget("text"),
            "No plan available",
        )
        self.assertEqual(
            panel.plan_status.cget("text"),
            "No plan",
        )
        self.assertEqual(
            panel.plan_step_count.cget("text"),
            "0 steps",
        )

    def test_plan_view_is_read_only(self):
        state = AgentInteractionState(
            plan=AgentPlanState(
                summary="Read-only plan",
                status="Ready",
                steps=("Inspect code",),
            )
        )

        panel = AgentInteractionPanel(self.root, state)

        self.assertEqual(
            panel.plan_steps.cget("state"),
            "disabled",
        )


if __name__ == "__main__":
    unittest.main()
