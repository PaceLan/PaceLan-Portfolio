import tkinter as tk
import unittest
from unittest.mock import Mock, patch

from ui.app import CodingAssistantApp
from ui.unified_transition import UnifiedTransitionKind
from ui.panel_transitions import TransitionDirection, TransitionPrimitive


class M267AppTransitionWiringTests(unittest.TestCase):

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

    def test_visual_experience_owns_unified_transition_controller(self):
        app = CodingAssistantApp(self.root)

        self.assertIsNotNone(
            app.visual_experience.transition_controller
        )
        self.assertEqual(
            app.visual_experience.transition_controller.current_kind,
            None,
        )

    def test_theme_toggle_uses_unified_transition(self):
        app = CodingAssistantApp(self.root)

        transition = app.visual_experience.transition_controller

        with patch.object(
            transition,
            "start",
            wraps=transition.start,
        ) as start, patch.object(
            transition,
            "enter",
            wraps=transition.enter,
        ) as enter, patch.object(
            transition,
            "complete",
            wraps=transition.complete,
        ) as complete:
            app._toggle_theme()

        start.assert_called_once_with(
            UnifiedTransitionKind.THEME,
            "theme",
        )
        enter.assert_called_once()
        complete.assert_called_once()

        self.assertEqual(
            transition.current_kind,
            UnifiedTransitionKind.THEME,
        )

    def test_workspace_open_uses_unified_transition(self):
        app = CodingAssistantApp(self.root)

        app.controller = Mock()
        app._set_project_state = Mock()
        app._load_project_tree = Mock()
        app.status_label = Mock()

        transition = app.visual_experience.transition_controller

        with patch(
            "ui.app.filedialog.askdirectory",
            return_value="C:\\TestProject",
        ), patch.object(
            transition,
            "start",
            wraps=transition.start,
        ) as start, patch.object(
            transition,
            "enter",
            wraps=transition.enter,
        ) as enter, patch.object(
            transition,
            "complete",
            wraps=transition.complete,
        ) as complete:
            app._choose_project()

        start.assert_called_once_with(
            UnifiedTransitionKind.WORKSPACE,
            "workspace",
            direction=TransitionDirection.NONE,
            primitive=TransitionPrimitive.CROSS_FADE,
        )
        enter.assert_called_once()
        complete.assert_called_once()

        app.controller.open_project.assert_called_once_with(
            "C:\\TestProject"
        )

    def test_agent_render_uses_unified_transition(self):
        app = CodingAssistantApp(self.root)

        state = Mock()
        state.task = None

        app.agent_panel = Mock()
        app.empty_state = Mock()

        projection = Mock()
        projection.stage = Mock()

        transition = app.visual_experience.transition_controller

        with patch(
            "ui.app.AgentVisualSystem.project",
            return_value=projection,
        ), patch.object(
            transition,
            "start",
            wraps=transition.start,
        ) as start, patch.object(
            transition,
            "enter",
            wraps=transition.enter,
        ) as enter, patch.object(
            transition,
            "complete",
            wraps=transition.complete,
        ) as complete:
            result = app._render_agent_state(state)

        self.assertIs(result, state)

        start.assert_called_once_with(
            UnifiedTransitionKind.AGENT,
            "agent",
            direction=TransitionDirection.NONE,
            primitive=TransitionPrimitive.FOCUS_DEPTH,
        )
        enter.assert_called_once()
        complete.assert_called_once()


if __name__ == "__main__":
    unittest.main()
