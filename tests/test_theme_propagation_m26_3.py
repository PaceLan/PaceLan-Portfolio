
import tkinter as tk
import unittest

from ui.agent_panel import AgentInteractionPanel
from ui.agent_state import AgentInteractionState
from ui.theme import DAY_THEME, NIGHT_THEME, ThemeState
from ui.visual_icons import VisualIconSet
from ui.visual_system import AgentPanelVisualSystem
from ui.workspace_empty_state import WorkspaceEmptyState


class M263ThemePropagationTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.root = tk.Tk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def test_icons_rebuild_with_theme_palette(self):
        icons = VisualIconSet(self.root)
        night_image = icons.image("brand")
        night_data = night_image.get(
            8,
            8,
        )

        icons.apply_theme(DAY_THEME)

        day_image = icons.image("brand")
        day_data = day_image.get(
            8,
            8,
        )

        self.assertNotEqual(
            icons.foreground,
            NIGHT_THEME.text_muted,
        )
        self.assertEqual(
            icons.foreground,
            DAY_THEME.text_muted,
        )
        self.assertIs(night_image, day_image)
        self.assertNotEqual(night_data, day_data)

    def test_empty_state_updates_runtime_palette(self):
        empty = WorkspaceEmptyState(self.root)
        empty.apply_theme(DAY_THEME)

        self.assertEqual(empty.top_color, DAY_THEME.background)
        self.assertEqual(empty.bottom_color, DAY_THEME.surface)
        self.assertEqual(empty.text_color, DAY_THEME.text)
        self.assertEqual(empty.muted_color, DAY_THEME.text_muted)
        self.assertEqual(empty.accent_color, DAY_THEME.accent)
        self.assertEqual(empty.cget("background"), DAY_THEME.background)

        empty.destroy()

    def test_agent_visual_system_updates_runtime_palette(self):
        panel = AgentInteractionPanel(
            self.root,
            AgentInteractionState(),
        )
        system = panel.visual_system

        system.apply_theme(DAY_THEME)

        self.assertEqual(system.background, DAY_THEME.surface_elevated)
        self.assertEqual(system.muted, DAY_THEME.text_muted)
        self.assertEqual(system.focus, DAY_THEME.accent)

        for outline in system.outlines.values():
            self.assertEqual(outline._theme_surface, DAY_THEME.surface)
            self.assertEqual(outline._theme_border, DAY_THEME.border)

        panel.destroy()

    def test_theme_state_palette_reaches_all_runtime_consumers(self):
        state = ThemeState()
        self.assertIs(state.palette, NIGHT_THEME)

        state = state.toggled()
        self.assertIs(state.palette, DAY_THEME)

        icons = VisualIconSet(self.root)
        empty = WorkspaceEmptyState(self.root)
        panel = AgentInteractionPanel(
            self.root,
            AgentInteractionState(),
        )
        system = panel.visual_system

        icons.apply_theme(state.palette)
        empty.apply_theme(state.palette)
        system.apply_theme(state.palette)

        self.assertEqual(empty.text_color, state.palette.text)
        self.assertEqual(system.focus, state.palette.accent)

        empty.destroy()
        panel.destroy()


if __name__ == "__main__":
    unittest.main()
