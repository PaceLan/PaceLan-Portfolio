import unittest
from dataclasses import FrozenInstanceError, is_dataclass

from ui.visual_components import Navigation, Panel, State, Workspace
from ui.visual_composition import DEFAULT_UX_COMPOSITION, UXComposition
from ui.visual_interaction import VisualInteractionState
from ui.visual_layout import WorkspaceLayout
from ui.visual_semantics import VisualSemantic
from ui.visual_tokens import DEFAULT_VISUAL_TOKENS, VisualTokens


class UXCompositionM197Tests(unittest.TestCase):

    def test_composition_module_exists(self):
        self.assertTrue(is_dataclass(UXComposition))

    def test_composition_is_immutable(self):
        composition = UXComposition()
        with self.assertRaises(FrozenInstanceError):
            composition.layout = WorkspaceLayout()

    def test_composition_contains_all_visual_layers(self):
        composition = DEFAULT_UX_COMPOSITION

        self.assertIsInstance(composition.tokens, VisualTokens)
        self.assertIsInstance(composition.panel, Panel)
        self.assertIsInstance(composition.navigation, Navigation)
        self.assertIsInstance(composition.workspace, Workspace)
        self.assertIsInstance(composition.state, State)
        self.assertIsInstance(composition.layout, WorkspaceLayout)
        self.assertIsInstance(
            composition.interaction,
            VisualInteractionState,
        )
        self.assertIsInstance(composition.semantics, VisualSemantic)

    def test_default_composition_reuses_default_tokens(self):
        self.assertIs(
            DEFAULT_UX_COMPOSITION.tokens,
            DEFAULT_VISUAL_TOKENS,
        )

    def test_composition_has_no_ui_framework_dependency(self):
        with open(
            "ui/visual_composition.py",
            encoding="utf-8-sig",
        ) as source_file:
            source = source_file.read()

        self.assertNotIn("tkinter", source.lower())
        self.assertNotIn("customtkinter", source.lower())


if __name__ == "__main__":
    unittest.main()
