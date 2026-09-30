import unittest

from ui.agent_state import AgentInteractionState, AgentUnderstandingState


class M214UnderstandingStateTests(unittest.TestCase):
    def test_understanding_state_supports_summary_and_details(self):
        state = AgentUnderstandingState(
            summary="Authentication flow",
            relevant_files=("src/auth.py", "src/session.py"),
            relevant_symbols=("AuthService", "Session"),
            relationships=("auth.py -> session.py",),
            dependencies=("src/session.py",),
        )

        self.assertEqual(state.summary, "Authentication flow")
        self.assertEqual(
            state.relevant_files,
            ("src/auth.py", "src/session.py"),
        )
        self.assertEqual(state.relevant_symbols, ("AuthService", "Session"))
        self.assertEqual(
            state.relationships,
            ("auth.py -> session.py",),
        )
        self.assertEqual(state.dependencies, ("src/session.py",))

    def test_default_understanding_is_empty(self):
        state = AgentUnderstandingState()

        self.assertEqual(state.summary, "No understanding available")
        self.assertEqual(state.relevant_files, ())
        self.assertEqual(state.relevant_symbols, ())
        self.assertEqual(state.relationships, ())
        self.assertEqual(state.dependencies, ())

    def test_understanding_state_is_immutable(self):
        state = AgentUnderstandingState(summary="x")

        with self.assertRaises((AttributeError, TypeError)):
            state.summary = "changed"

    def test_interaction_state_preserves_understanding(self):
        understanding = AgentUnderstandingState(
            summary="Authentication flow",
            relevant_files=("src/auth.py",),
        )

        state = AgentInteractionState(understanding=understanding)

        self.assertIs(state.understanding, understanding)
        self.assertIsInstance(
            state.understanding,
            AgentUnderstandingState,
        )


if __name__ == "__main__":
    unittest.main()


class M214UnderstandingPanelTests(unittest.TestCase):
    def test_panel_exposes_understanding_section(self):
        import tkinter as tk
        from ui.agent_panel import AgentInteractionPanel

        root = tk.Tk()
        root.withdraw()
        try:
            panel = AgentInteractionPanel(root)
            self.assertIn("Understanding", panel.section_titles)
            self.assertTrue(hasattr(panel, "understanding_summary"))
            self.assertTrue(hasattr(panel, "understanding_files"))
            self.assertTrue(hasattr(panel, "understanding_symbols"))
            self.assertTrue(hasattr(panel, "understanding_relationships"))
            self.assertTrue(hasattr(panel, "understanding_dependencies"))
        finally:
            root.destroy()

    def test_panel_renders_understanding_state(self):
        import tkinter as tk
        from ui.agent_panel import AgentInteractionPanel

        root = tk.Tk()
        root.withdraw()
        try:
            state = AgentInteractionState(
                understanding=AgentUnderstandingState(
                    summary="Authentication flow",
                    relevant_files=("src/auth.py", "src/session.py"),
                    relevant_symbols=("AuthService", "Session"),
                    relationships=("auth.py -> session.py",),
                    dependencies=("src/session.py",),
                )
            )
            panel = AgentInteractionPanel(root, state)

            self.assertEqual(
                panel.understanding_summary.cget("text"),
                "Authentication flow",
            )
            self.assertEqual(
                panel.understanding_files.cget("text"),
                "Files: 2",
            )
            self.assertEqual(
                panel.understanding_symbols.cget("text"),
                "Symbols: 2",
            )
            self.assertEqual(
                panel.understanding_relationships.cget("text"),
                "Relationships: 1",
            )
            self.assertEqual(
                panel.understanding_dependencies.cget("text"),
                "Dependencies: 1",
            )
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
