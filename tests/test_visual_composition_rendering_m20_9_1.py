import tkinter as tk
import unittest

from ui.app import CodingAssistantApp
from ui.visual_composition import UXComposition
from ui.visual_tokens import VisualTokens


class TestVisualCompositionRenderingM2091(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        self.root.destroy()

    def test_app_creates_visual_renderer_from_composition(self):
        composition = UXComposition()
        app = CodingAssistantApp(self.root, composition=composition)

        self.assertIs(app.composition, composition)
        self.assertIs(app.visual_renderer.composition, composition)
        self.assertIs(app.visual_renderer.tokens, composition.tokens)

    def test_header_consumes_composition_typography(self):
        composition = UXComposition()
        app = CodingAssistantApp(self.root, composition=composition)

        font = app.visual_renderer.style.lookup(
            "PacePilot.Header.TLabel",
            "font",
        )

        self.assertIn(str(composition.tokens.typography["size_xl"]), str(font))

    def test_navigation_and_workspace_consume_surface_token(self):
        composition = UXComposition()
        app = CodingAssistantApp(self.root, composition=composition)

        navigation_background = app.visual_renderer.style.lookup(
            "PacePilot.Panel.TLabelframe",
            "background",
        )
        workspace_background = app.visual_renderer.style.lookup(
            "PacePilot.Panel.TLabelframe",
            "background",
        )

        self.assertEqual(
            navigation_background,
            composition.tokens.colors["surface"],
        )
        self.assertEqual(
            workspace_background,
            composition.tokens.colors["surface"],
        )

    def test_tree_consumes_composition_colors(self):
        composition = UXComposition()
        app = CodingAssistantApp(self.root, composition=composition)

        background = app.visual_renderer.style.lookup(
            "PacePilot.Treeview",
            "background",
        )
        foreground = app.visual_renderer.style.lookup(
            "PacePilot.Treeview",
            "foreground",
        )

        self.assertEqual(background, composition.tokens.colors["surface"])
        self.assertEqual(foreground, composition.tokens.colors["text"])

    def test_status_consumes_elevated_surface_token(self):
        composition = UXComposition()
        app = CodingAssistantApp(self.root, composition=composition)

        background = app.visual_renderer.style.lookup(
            "PacePilot.Status.TLabel",
            "background",
        )

        self.assertEqual(
            background,
            composition.tokens.colors["surface_elevated"],
        )

    def test_file_viewer_consumes_composition_tokens(self):
        composition = UXComposition()
        app = CodingAssistantApp(self.root, composition=composition)

        self.assertEqual(
            app.file_viewer.cget("background"),
            composition.tokens.colors["surface"],
        )
        self.assertEqual(
            app.file_viewer.cget("foreground"),
            composition.tokens.colors["text"],
        )
        self.assertEqual(
            app.file_viewer.cget("insertbackground"),
            composition.tokens.colors["text"],
        )

    def test_custom_tokens_reach_rendered_widgets(self):
        tokens = VisualTokens(
            colors={
                "background": "#010203",
                "surface": "#111213",
                "surface_elevated": "#212223",
                "text": "#313233",
                "text_secondary": "#414243",
                "text_muted": "#515253",
                "border": "#616263",
                "accent": "#717273",
                "info": "#818283",
                "success": "#919293",
                "warning": "#A1A2A3",
                "error": "#B1B2B3",
                "agent_running": "#C1C2C3",
            },
            typography={
                "font_family": "TkDefaultFont",
                "size_xs": 10,
                "size_sm": 11,
                "size_md": 12,
                "size_lg": 14,
                "size_xl": 18,
                "size_xxl": 20,
                "weight_regular": "normal",
                "weight_medium": "bold",
            },
            spacing={
                "xs": 4,
                "sm": 8,
                "md": 12,
                "lg": 16,
                "xl": 24,
                "xxl": 32,
            },
            radius={
                "sm": 4,
                "md": 8,
                "lg": 12,
            },
            borders={
                "thin": 1,
                "medium": 2,
            },
        )

        composition = UXComposition(tokens=tokens)
        app = CodingAssistantApp(self.root, composition=composition)

        self.assertEqual(
            app.file_viewer.cget("background"),
            "#111213",
        )
        self.assertEqual(
            app.file_viewer.cget("foreground"),
            "#313233",
        )
        self.assertEqual(
            app.visual_renderer.style.lookup(
                "PacePilot.Treeview",
                "background",
            ),
            "#111213",
        )
        self.assertEqual(
            app.visual_renderer.style.lookup(
                "PacePilot.Header.TLabel",
                "foreground",
            ),
            "#313233",
        )


if __name__ == "__main__":
    unittest.main()
