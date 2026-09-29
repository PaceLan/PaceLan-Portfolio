import tkinter as tk
import unittest

from ui.visual_composition import UXComposition
from ui.visual_renderer import VisualRenderer


class TestVisualStatusStateRenderingM2093(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.renderer = VisualRenderer(
            self.root,
            UXComposition(),
        )
        self.widget = tk.Label(self.root)

    def tearDown(self):
        self.widget.destroy()

    def test_default_status_remains_ready(self):
        self.renderer.apply_status(self.widget)

        self.assertEqual(
            self.widget.cget("foreground"),
            self.renderer.tokens.colors["info"],
        )

    def test_running_state_uses_running_semantic(self):
        self.renderer.apply_status(
            self.widget,
            "running",
        )

        self.assertEqual(
            self.widget.cget("foreground"),
            self.renderer.tokens.colors["agent_running"],
        )

    def test_success_state_uses_success_semantic(self):
        self.renderer.apply_status(
            self.widget,
            "success",
        )

        self.assertEqual(
            self.widget.cget("foreground"),
            self.renderer.tokens.colors["success"],
        )

    def test_warning_state_uses_warning_semantic(self):
        self.renderer.apply_status(
            self.widget,
            "warning",
        )

        self.assertEqual(
            self.widget.cget("foreground"),
            self.renderer.tokens.colors["warning"],
        )

    def test_error_state_uses_error_semantic(self):
        self.renderer.apply_status(
            self.widget,
            "error",
        )

        self.assertEqual(
            self.widget.cget("foreground"),
            self.renderer.tokens.colors["error"],
        )

    def test_idle_state_uses_neutral_semantic(self):
        self.renderer.apply_status(
            self.widget,
            "idle",
        )

        self.assertEqual(
            self.widget.cget("foreground"),
            self.renderer.tokens.colors["text_secondary"],
        )

    def test_waiting_state_uses_pending_semantic(self):
        self.renderer.apply_status(
            self.widget,
            "waiting",
        )

        self.assertEqual(
            self.widget.cget("foreground"),
            self.renderer.tokens.colors["warning"],
        )

    def test_status_state_does_not_mutate_composition(self):
        composition = UXComposition()
        renderer = VisualRenderer(self.root, composition)

        renderer.apply_status(self.widget, "running")

        self.assertEqual(
            composition.interaction.ready,
            "ready",
        )

    def test_invalid_state_is_rejected(self):
        with self.assertRaises(KeyError):
            self.renderer.apply_status(
                self.widget,
                "invalid-state",
            )


if __name__ == "__main__":
    unittest.main()
