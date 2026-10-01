import unittest

from ui.panel_transitions import TransitionDirection, TransitionPhase
from ui.unified_transition import (
    UnifiedTransitionController,
    UnifiedTransitionKind,
)


class UnifiedTransitionTests(unittest.TestCase):
    def test_start_opening(self):
        controller = UnifiedTransitionController()

        transition = controller.start(
            UnifiedTransitionKind.OPENING,
            "loading",
        )

        self.assertEqual(transition.kind, UnifiedTransitionKind.OPENING)
        self.assertEqual(transition.target, "loading")
        self.assertEqual(transition.phase, TransitionPhase.ENTERING)
        self.assertTrue(transition.active)

    def test_workspace_switch_uses_existing_panel_engine(self):
        controller = UnifiedTransitionController()
        controller.start(UnifiedTransitionKind.OPENING, "opening")
        controller.complete()

        transition = controller.start(
            UnifiedTransitionKind.WORKSPACE,
            "workspace",
            direction=TransitionDirection.FORWARD,
        )

        self.assertEqual(transition.source, "opening")
        self.assertEqual(transition.target, "workspace")
        self.assertEqual(
            controller.panel_transition.direction,
            TransitionDirection.FORWARD,
        )

    def test_enter_and_complete(self):
        controller = UnifiedTransitionController()
        controller.start(UnifiedTransitionKind.GREETING, "greeting")

        entering = controller.enter()
        self.assertEqual(entering.phase, TransitionPhase.ENTERING)

        completed = controller.complete()
        self.assertEqual(completed.phase, TransitionPhase.COMPLETE)
        self.assertEqual(controller.current_panel, "greeting")

    def test_theme_is_a_first_class_transition(self):
        controller = UnifiedTransitionController()

        transition = controller.start(
            UnifiedTransitionKind.THEME,
            "night",
        )

        self.assertEqual(transition.kind, UnifiedTransitionKind.THEME)
        self.assertEqual(transition.target, "night")

    def test_empty_target_rejected(self):
        controller = UnifiedTransitionController()

        with self.assertRaises(ValueError):
            controller.start(UnifiedTransitionKind.LOADING, "")

    def test_negative_duration_rejected(self):
        with self.assertRaises(ValueError):
            UnifiedTransitionController(duration_ms=-1)


if __name__ == "__main__":
    unittest.main()
