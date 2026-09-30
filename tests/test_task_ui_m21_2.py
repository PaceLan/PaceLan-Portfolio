import unittest

from ui.agent_state import AgentInteractionState, AgentTaskState


class M212TaskStateTests(unittest.TestCase):

    def test_task_state_supports_task_description(self):
        state = AgentTaskState(
            title="Fix authentication",
            description="Investigate the login failure.",
            status="Ready",
        )

        self.assertEqual(state.title, "Fix authentication")
        self.assertEqual(
            state.description,
            "Investigate the login failure.",
        )
        self.assertEqual(state.status, "Ready")

    def test_default_task_is_empty(self):
        state = AgentTaskState()

        self.assertEqual(state.title, "No task")
        self.assertEqual(state.description, "No task selected")
        self.assertEqual(state.status, "No task")

    def test_task_state_is_immutable(self):
        state = AgentTaskState()

        with self.assertRaises(Exception):
            state.description = "changed"

    def test_interaction_state_preserves_task_state(self):
        task = AgentTaskState(
            title="Build feature",
            description="Implement the requested feature.",
            status="Ready",
        )
        state = AgentInteractionState(task=task)

        self.assertEqual(state.task, task)


    def test_panel_renders_task_description(self):
        import tkinter as tk

        from ui.agent_panel import AgentInteractionPanel

        root = tk.Tk()
        root.withdraw()

        try:
            state = AgentInteractionState(
                task=AgentTaskState(
                    title="Build feature",
                    description="Implement the requested feature.",
                    status="Ready",
                )
            )

            panel = AgentInteractionPanel(root, state)

            self.assertEqual(
                panel.task_description.cget("text"),
                "Implement the requested feature.",
            )
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
