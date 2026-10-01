import tkinter as tk
import unittest

from ui.ambient_effects import AmbientFieldController
from ui.opening_experience import OpeningConfig, OpeningExperience
from ui.theme import ThemeState


class OpeningExperienceM264Tests(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()

    def tearDown(self):
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def test_default_config(self):
        config = OpeningConfig()
        self.assertEqual(config.mark, "PacePilot")
        self.assertEqual(config.greeting, "Welcome back")
        self.assertGreater(config.duration_ms, 0)
        self.assertGreater(config.fade_in_ms, 0)
        self.assertGreater(config.fade_out_ms, 0)

    def test_can_complete(self):
        opening = OpeningExperience(self.root)
        opening.complete()
        self.assertTrue(opening.completed)

    def test_start_sets_started_state(self):
        opening = OpeningExperience(self.root)
        opening.start()
        self.assertTrue(opening._started)
        self.assertFalse(opening.completed)
        opening.complete()

    def test_completion_callback_runs_once(self):
        calls = []
        opening = OpeningExperience(self.root)
        opening.complete(lambda: calls.append("done"))
        opening.complete(lambda: calls.append("again"))
        self.assertEqual(calls, ["done"])

    def test_uses_shared_ambient_and_theme(self):
        ambient = AmbientFieldController()
        theme = ThemeState()
        opening = OpeningExperience(
            self.root,
            ambient=ambient,
            theme_state=theme,
        )
        self.assertIs(opening.ambient, ambient)
        self.assertIs(opening.theme_state, theme)
        opening.complete()

    def test_greeting_is_rendered(self):
        opening = OpeningExperience(
            self.root,
            config=OpeningConfig(greeting="Good evening"),
        )
        opening._render(1.0, 0)
        items = opening._canvas.find_all()
        texts = [opening._canvas.itemcget(item, "text") for item in items if opening._canvas.type(item) == "text"]
        self.assertIn("PacePilot", texts)
        self.assertIn("Good evening", texts)
        opening.complete()


if __name__ == "__main__":
    unittest.main()

