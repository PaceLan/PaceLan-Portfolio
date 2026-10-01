import unittest

from ui.theme import DAY_THEME, NIGHT_THEME, ThemeState
from ui.visual_renderer import VisualRenderer


class _FakeStyle:
    def __init__(self):
        self.configured = []

    def configure(self, name, **kwargs):
        self.configured.append((name, kwargs))


class _FakeWidget:
    def __init__(self, widget_class):
        self._class = widget_class

    def winfo_class(self):
        return self._class


class M263ThemeRendererTests(unittest.TestCase):

    def _renderer(self, state):
        renderer = object.__new__(VisualRenderer)
        renderer.theme_state = state
        renderer.style = _FakeStyle()
        return renderer

    def test_night_surface_style_uses_night_palette(self):
        renderer = self._renderer(ThemeState("night"))
        widget = _FakeWidget("TLabelframe")

        style_name = renderer.style_name_for_surface(widget)

        self.assertIn("TLabelframe", style_name)
        self.assertEqual(
            renderer.style.configured[-1][1]["background"],
            NIGHT_THEME.surface,
        )

    def test_day_surface_style_uses_day_palette(self):
        renderer = self._renderer(ThemeState("day"))
        widget = _FakeWidget("TLabelframe")

        renderer.style_name_for_surface(widget)

        self.assertEqual(
            renderer.style.configured[-1][1]["background"],
            DAY_THEME.surface,
        )

    def test_theme_toggle_produces_distinct_surface_style(self):
        widget = _FakeWidget("TLabelframe")

        night = self._renderer(ThemeState("night"))
        day = self._renderer(ThemeState("day"))

        night.style_name_for_surface(widget)
        day.style_name_for_surface(widget)

        self.assertNotEqual(
            night.style.configured[-1][1]["background"],
            day.style.configured[-1][1]["background"],
        )


if __name__ == "__main__":
    unittest.main()
