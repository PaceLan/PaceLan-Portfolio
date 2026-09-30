import unittest

from ui.panel_transitions import (
    PanelTransition,
    PanelTransitionController,
    TransitionDirection,
    TransitionPhase,
)


class M227PanelTransitionTests(unittest.TestCase):
    def test_default_transition_is_idle(self):
        transition = PanelTransition()
        self.assertEqual(transition.phase, TransitionPhase.IDLE)
        self.assertFalse(transition.active)

    def test_duration_must_not_be_negative(self):
        with self.assertRaises(ValueError):
            PanelTransition(duration_ms=-1)

    def test_controller_starts_without_current_panel(self):
        controller = PanelTransitionController()
        transition = controller.start("agent")

        self.assertIsNone(transition.source)
        self.assertEqual(transition.target, "agent")
        self.assertEqual(transition.phase, TransitionPhase.ENTERING)
        self.assertTrue(transition.active)

    def test_controller_exits_current_panel_before_entering_target(self):
        controller = PanelTransitionController()
        controller.start("workspace")
        controller.complete()

        transition = controller.start(
            "agent",
            direction=TransitionDirection.FORWARD,
        )

        self.assertEqual(transition.source, "workspace")
        self.assertEqual(transition.target, "agent")
        self.assertEqual(transition.phase, TransitionPhase.EXITING)
        self.assertTrue(transition.active)

    def test_enter_advances_transition(self):
        controller = PanelTransitionController()
        controller.start("workspace")
        controller.complete()

        controller.start("agent")
        transition = controller.enter()

        self.assertEqual(transition.phase, TransitionPhase.ENTERING)
        self.assertTrue(transition.active)

    def test_complete_commits_target_panel(self):
        controller = PanelTransitionController()
        controller.start("workspace")
        transition = controller.complete()

        self.assertEqual(controller.current_panel, "workspace")
        self.assertEqual(transition.phase, TransitionPhase.COMPLETE)
        self.assertFalse(transition.active)

    def test_same_panel_does_not_create_active_transition(self):
        controller = PanelTransitionController()
        controller.start("agent")
        controller.complete()

        transition = controller.start("agent")

        self.assertEqual(transition.phase, TransitionPhase.COMPLETE)
        self.assertFalse(transition.active)
        self.assertEqual(controller.current_panel, "agent")

    def test_reset_returns_to_idle(self):
        controller = PanelTransitionController()
        controller.start("agent")
        transition = controller.reset()

        self.assertIsNone(controller.current_panel)
        self.assertEqual(transition.phase, TransitionPhase.IDLE)
        self.assertFalse(transition.active)


if __name__ == "__main__":
    unittest.main()
