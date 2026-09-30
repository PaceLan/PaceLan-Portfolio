import tkinter as tk
import unittest

from ui.app import CodingAssistantApp
from ui.visual_composition import DEFAULT_UX_COMPOSITION, UXComposition
from ui.visual_layout import WorkspaceLayout


class M208VisualCompositionAppTests(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_app_defaults_to_default_ux_composition(self):
        app = CodingAssistantApp(self.root)

        self.assertIs(app.composition, DEFAULT_UX_COMPOSITION)

    def test_app_accepts_explicit_ux_composition(self):
        composition = UXComposition()

        app = CodingAssistantApp(
            self.root,
            composition=composition,
        )

        self.assertIs(app.composition, composition)

    def test_app_uses_composition_layout_by_default(self):
        composition = UXComposition()

        app = CodingAssistantApp(
            self.root,
            composition=composition,
        )

        self.assertIs(app.layout, composition.layout)

    def test_explicit_layout_preserves_legacy_override(self):
        composition = UXComposition()
        layout = WorkspaceLayout()

        app = CodingAssistantApp(
            self.root,
            layout=layout,
            composition=composition,
        )

        self.assertIs(app.composition, composition)
        self.assertIs(app.layout, layout)

    def test_composition_is_ux_composition_contract(self):
        app = CodingAssistantApp(self.root)

        self.assertIsInstance(app.composition, UXComposition)


if __name__ == "__main__":
    unittest.main()
