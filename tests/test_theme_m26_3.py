import unittest

from ui.theme import DAY_THEME, NIGHT_THEME, ThemeState, palette_for


class M263ThemeTests(unittest.TestCase):

    def test_default_theme_is_night(self):
        state = ThemeState()
        self.assertEqual(state.mode, "night")
        self.assertTrue(state.is_night)
        self.assertEqual(state.palette, NIGHT_THEME)

    def test_toggle_switches_day_and_night(self):
        night = ThemeState("night")
        day = night.toggled()

        self.assertEqual(day.mode, "day")
        self.assertFalse(day.is_night)
        self.assertEqual(day.palette, DAY_THEME)
        self.assertEqual(day.toggled(), night)

    def test_day_and_night_have_distinct_surface_palettes(self):
        self.assertNotEqual(
            NIGHT_THEME.background,
            DAY_THEME.background,
        )
        self.assertNotEqual(
            NIGHT_THEME.surface,
            DAY_THEME.surface,
        )
        self.assertNotEqual(
            NIGHT_THEME.text,
            DAY_THEME.text,
        )

    def test_palette_lookup_is_deterministic(self):
        self.assertEqual(palette_for("night"), NIGHT_THEME)
        self.assertEqual(palette_for("day"), DAY_THEME)


if __name__ == "__main__":
    unittest.main()
