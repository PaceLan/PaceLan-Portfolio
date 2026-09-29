import tkinter as tk
import unittest

from ui.app import CodingAssistantApp
from ui.visual_composition import UXComposition
from ui.visual_interaction import VisualInteractionState
from ui.visual_renderer import VisualRenderer
from ui.visual_semantic_mapper import VisualSemanticMapper
from ui.visual_semantics import VisualSemantic


class TestVisualSemanticRenderingM2092(unittest.TestCase):
    def setUp(self):
        self.mapper = VisualSemanticMapper()
        self.states = VisualInteractionState()
        self.semantics = VisualSemantic()

    def test_all_interaction_states_have_semantic_mapping(self):
        expected = {
            self.states.idle: self.semantics.neutral,
            self.states.ready: self.semantics.informative,
            self.states.running: self.semantics.active,
            self.states.waiting: self.semantics.pending,
            self.states.success: self.semantics.positive,
            self.states.warning: self.semantics.caution,
            self.states.error: self.semantics.negative,
        }

        for state, semantic in expected.items():
            with self.subTest(state=state):
                self.assertEqual(
                    self.mapper.semantic_for(state),
                    semantic,
                )

    def test_semantic_mapping_is_deterministic(self):
        states = (
            self.states.idle,
            self.states.ready,
            self.states.running,
            self.states.waiting,
            self.states.success,
            self.states.warning,
            self.states.error,
        )

        for state in states:
            with self.subTest(state=state):
                self.assertEqual(
                    self.mapper.semantic_for(state),
                    self.mapper.semantic_for(state),
                )

    def test_semantic_values_are_valid_visual_semantics(self):
        valid_semantics = {
            self.semantics.neutral,
            self.semantics.informative,
            self.semantics.active,
            self.semantics.pending,
            self.semantics.positive,
            self.semantics.caution,
            self.semantics.negative,
        }

        for state in (
            self.states.idle,
            self.states.ready,
            self.states.running,
            self.states.waiting,
            self.states.success,
            self.states.warning,
            self.states.error,
        ):
            with self.subTest(state=state):
                self.assertIn(
                    self.mapper.semantic_for(state),
                    valid_semantics,
                )

    def test_all_semantics_have_color_token_mapping(self):
        expected = {
            self.semantics.neutral: "text_secondary",
            self.semantics.informative: "info",
            self.semantics.active: "agent_running",
            self.semantics.pending: "warning",
            self.semantics.positive: "success",
            self.semantics.caution: "warning",
            self.semantics.negative: "error",
        }

        for semantic, token_name in expected.items():
            with self.subTest(semantic=semantic):
                self.assertEqual(
                    self.mapper.color_token_for(semantic),
                    token_name,
                )

    def test_color_token_mapping_uses_existing_visual_tokens(self):
        expected_tokens = {
            "text_secondary",
            "info",
            "agent_running",
            "warning",
            "success",
            "error",
        }

        for semantic in (
            self.semantics.neutral,
            self.semantics.informative,
            self.semantics.active,
            self.semantics.pending,
            self.semantics.positive,
            self.semantics.caution,
            self.semantics.negative,
        ):
            with self.subTest(semantic=semantic):
                self.assertIn(
                    self.mapper.color_token_for(semantic),
                    expected_tokens,
                )

    def test_renderer_applies_semantic_color_to_status(self):
        root = tk.Tk()
        root.withdraw()

        try:
            composition = UXComposition()
            renderer = VisualRenderer(root, composition)
            widget = tk.Label(root)

            renderer.apply_status_semantic(
                widget,
                self.semantics.positive,
            )

            self.assertEqual(
                widget.cget("foreground"),
                composition.tokens.colors["success"],
            )
        finally:
            root.destroy()

    def test_renderer_semantic_color_uses_mapper_contract(self):
        root = tk.Tk()
        root.withdraw()

        try:
            composition = UXComposition()
            renderer = VisualRenderer(root, composition)

            semantic = self.mapper.semantic_for(self.states.running)
            token_name = self.mapper.color_token_for(semantic)

            widget = tk.Label(root)

            renderer.apply_status_semantic(widget, semantic)

            self.assertEqual(
                widget.cget("foreground"),
                composition.tokens.colors[token_name],
            )
        finally:
            root.destroy()

    def test_app_initial_status_uses_ready_semantic(self):
        root = tk.Tk()
        root.withdraw()

        try:
            composition = UXComposition()
            app = CodingAssistantApp(root, composition=composition)

            expected_color = composition.tokens.colors["info"]

            self.assertEqual(
                app.status_label.cget("foreground"),
                expected_color,
            )
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
