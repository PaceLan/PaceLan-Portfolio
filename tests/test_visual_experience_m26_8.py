import tkinter as tk
import unittest
from unittest import mock

from ui.app import CodingAssistantApp
from ui.visual_experience import VisualExperienceController
from ui.ambient_runtime import AmbientRuntime


class M268VisualExperienceTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        try:
            cls.root = tk.Tk()
            cls.root.withdraw()
        except tk.TclError as error:
            raise unittest.SkipTest(
                f"Tk unavailable in test environment: {error}"
            )

    @classmethod
    def tearDownClass(cls):
        try:
            cls.root.destroy()
        except tk.TclError:
            pass

    def test_app_owns_visual_experience_controller(self):
        app = CodingAssistantApp(self.root)

        self.assertIsInstance(
            app.visual_experience,
            VisualExperienceController,
        )

    def test_visual_experience_contains_visual_orchestration_state(self):
        app = CodingAssistantApp(self.root)

        self.assertIs(
            app.theme_state,
            app.visual_experience.theme_state,
        )
        self.assertIsNotNone(
            app.visual_experience.ambient,
        )
        self.assertIsNotNone(
            app.visual_experience.transition_controller,
        )

    def test_visual_experience_coordinates_theme_transition(self):
        app = CodingAssistantApp(self.root)

        before = app.theme_state.is_night

        app.visual_experience.toggle_theme()

        self.assertNotEqual(
            app.visual_experience.theme_state.is_night,
            before,
        )
        self.assertIs(
            app.theme_state,
            app.visual_experience.theme_state,
        )


    def test_theme_toggle_synchronizes_existing_visual_surfaces(self):
        app = CodingAssistantApp(self.root)

        app.icons.apply_theme = mock.Mock()
        app.empty_state.apply_theme = mock.Mock()
        app.agent_panel.visual_system.apply_theme = mock.Mock()

        app.visual_experience.toggle_theme()

        palette = app.theme_state.palette
        app.icons.apply_theme.assert_called_once_with(palette)
        app.empty_state.apply_theme.assert_called_once_with(palette)
        app.agent_panel.visual_system.apply_theme.assert_called_once_with(palette)

    def test_visual_experience_exposes_ambient_runtime(self):
        app = CodingAssistantApp(self.root)

        self.assertIsInstance(
            app.visual_experience.ambient_runtime,
            AmbientRuntime,
        )

    def test_ambient_runtime_start_is_idempotent(self):
        app = CodingAssistantApp(self.root)
        runtime = app.visual_experience.ambient_runtime

        runtime.start()
        first_after = runtime._after

        runtime.start()

        self.assertIs(
            runtime._after,
            first_after,
        )

        runtime.stop()

    def test_ambient_runtime_start_and_stop_control_field(self):
        app = CodingAssistantApp(self.root)
        runtime = app.visual_experience.ambient_runtime

        runtime.start()
        self.assertTrue(runtime.ambient.state.enabled)

        runtime.stop()
        self.assertFalse(runtime.ambient.state.enabled)

    def test_ambient_runtime_tracks_theme_background(self):
        app = CodingAssistantApp(self.root)
        runtime = app.visual_experience.ambient_runtime

        runtime.build()
        before = runtime.canvas.cget("bg")

        app.visual_experience.toggle_theme()
        runtime.render()

        after = runtime.canvas.cget("bg")

        self.assertNotEqual(before, after)
        self.assertEqual(
            after,
            app.visual_experience.theme_state.palette.background,
        )

        runtime.stop()



if __name__ == "__main__":
    unittest.main()
