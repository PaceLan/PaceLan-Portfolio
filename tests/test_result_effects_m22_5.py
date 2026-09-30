import unittest

from ui.animation import AnimationKind
from ui.result_effects import ResultEffectMapper, ResultVisualState


class M225ResultEffectsTests(unittest.TestCase):

    def test_execution_to_completed_is_positive_and_terminal(self):
        effect = ResultEffectMapper.effect(
            ResultVisualState.EXECUTING,
            ResultVisualState.COMPLETED,
        )

        self.assertIsNotNone(effect)
        self.assertEqual(effect.semantic, "positive")
        self.assertEqual(effect.animation.kind, AnimationKind.FADE)
        self.assertTrue(effect.terminal)

    def test_execution_to_warning_is_caution(self):
        effect = ResultEffectMapper.effect(
            ResultVisualState.EXECUTING,
            ResultVisualState.WARNING,
        )

        self.assertIsNotNone(effect)
        self.assertEqual(effect.semantic, "caution")
        self.assertEqual(effect.animation.kind, AnimationKind.PULSE)
        self.assertFalse(effect.terminal)

    def test_execution_to_failed_is_negative(self):
        effect = ResultEffectMapper.effect(
            ResultVisualState.EXECUTING,
            ResultVisualState.FAILED,
        )

        self.assertIsNotNone(effect)
        self.assertEqual(effect.semantic, "negative")
        self.assertFalse(effect.terminal)

    def test_failed_to_recovery_is_informative(self):
        effect = ResultEffectMapper.effect(
            ResultVisualState.FAILED,
            ResultVisualState.RECOVERY,
        )

        self.assertIsNotNone(effect)
        self.assertEqual(effect.semantic, "informative")

    def test_failed_to_ended_is_terminal(self):
        effect = ResultEffectMapper.effect(
            ResultVisualState.FAILED,
            ResultVisualState.ENDED,
        )

        self.assertIsNotNone(effect)
        self.assertEqual(effect.semantic, "negative")
        self.assertTrue(effect.terminal)

    def test_recovery_can_return_to_execution(self):
        effect = ResultEffectMapper.effect(
            ResultVisualState.RECOVERY,
            ResultVisualState.EXECUTING,
        )

        self.assertIsNotNone(effect)
        self.assertEqual(effect.semantic, "active")
        self.assertEqual(effect.animation.kind, AnimationKind.PULSE)

    def test_unknown_result_transition_has_no_effect(self):
        self.assertFalse(
            ResultEffectMapper.has_effect(
                ResultVisualState.COMPLETED,
                ResultVisualState.EXECUTING,
            )
        )
        self.assertIsNone(
            ResultEffectMapper.effect(
                ResultVisualState.COMPLETED,
                ResultVisualState.EXECUTING,
            )
        )

    def test_effect_is_immutable(self):
        effect = ResultEffectMapper.effect(
            ResultVisualState.EXECUTING,
            ResultVisualState.COMPLETED,
        )

        with self.assertRaises(Exception):
            effect.semantic = "negative"


if __name__ == "__main__":
    unittest.main()