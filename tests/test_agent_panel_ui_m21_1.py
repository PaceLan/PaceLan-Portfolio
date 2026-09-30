import tkinter as tk
import unittest

from ui.agent_panel import AgentInteractionPanel
from ui.agent_state import AgentInteractionState


class M211AgentPanelTests(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_panel_is_constructible(self):
        panel = AgentInteractionPanel(
            self.root,
            AgentInteractionState(),
        )
        self.assertIsNotNone(panel)

    def test_panel_contains_agent_sections(self):
        panel = AgentInteractionPanel(
            self.root,
            AgentInteractionState(),
        )

        self.assertIn("Agent", panel.section_titles)
        self.assertIn("Current Task", panel.section_titles)
        self.assertIn("Plan", panel.section_titles)
        self.assertIn("Execution", panel.section_titles)
        self.assertIn("Result", panel.section_titles)

    def test_empty_state_is_rendered(self):
        panel = AgentInteractionPanel(
            self.root,
            AgentInteractionState(),
        )

        self.assertEqual(panel.task_value.cget("text"), "No task")
        self.assertEqual(panel.plan_value.cget("text"), "No plan available")
        self.assertEqual(panel.execution_value.cget("text"), "Idle")
        self.assertEqual(panel.result_value.cget("text"), "No result available")

    def test_panel_updates_from_state(self):
        state = AgentInteractionState()
        panel = AgentInteractionPanel(self.root, state)

        updated = AgentInteractionState(
            task=state.task.__class__(
                title="Fix authentication",
                status="Ready",
            ),
            plan=state.plan.__class__(
                summary="3 steps",
                status="Ready",
            ),
            execution=state.execution.__class__(
                status="Running",
            ),
            result=state.result.__class__(
                summary="No result yet",
                status="Pending",
            ),
        )

        panel.render(updated)

        self.assertEqual(panel.task_value.cget("text"), "Fix authentication")
        self.assertEqual(panel.plan_value.cget("text"), "3 steps")
        self.assertEqual(panel.execution_value.cget("text"), "Running")
        self.assertEqual(panel.result_value.cget("text"), "No result yet")


if __name__ == "__main__":
    unittest.main()
