import unittest

from ui.ambient_effects import (
    AmbientEffect,
    AmbientEffectController,
    AmbientEffectState,
    AmbientPhase,
)


class M228AmbientEffectsTests(unittest.TestCase):
    def test_default_state_is_idle(self):
        state = AmbientEffectState()

        self.assertEqual(state.effect, AmbientEffect.NONE)
        self.assertEqual(state.phase, AmbientPhase.IDLE)
        self.assertFalse(state.active)

    def test_intensity_must_be_in_range(self):
        with self.assertRaises(ValueError):
            AmbientEffectState(intensity=1.1)

        with self.assertRaises(ValueError):
            AmbientEffectState(intensity=-0.1)

    def test_start_activates_effect(self):
        controller = AmbientEffectController()
        state = controller.start(AmbientEffect.BREATHING)

        self.assertEqual(state.effect, AmbientEffect.BREATHING)
        self.assertEqual(state.phase, AmbientPhase.ACTIVE)
        self.assertTrue(state.active)

    def test_start_accepts_explicit_intensity(self):
        controller = AmbientEffectController()
        state = controller.start(
            AmbientEffect.ACTIVITY,
            intensity=0.6,
        )

        self.assertEqual(state.intensity, 0.6)

    def test_pause_and_resume_preserve_configuration(self):
        controller = AmbientEffectController()
        controller.start(AmbientEffect.FOCUS, intensity=0.5)

        paused = controller.pause()
        self.assertEqual(paused.phase, AmbientPhase.PAUSED)
        self.assertEqual(paused.intensity, 0.5)

        resumed = controller.resume()
        self.assertEqual(resumed.phase, AmbientPhase.ACTIVE)
        self.assertEqual(resumed.effect, AmbientEffect.FOCUS)
        self.assertEqual(resumed.intensity, 0.5)

    def test_stop_returns_to_idle(self):
        controller = AmbientEffectController()
        controller.start(AmbientEffect.ACTIVITY)

        state = controller.stop()

        self.assertEqual(state.effect, AmbientEffect.NONE)
        self.assertEqual(state.phase, AmbientPhase.IDLE)
        self.assertFalse(state.active)

    def test_none_effect_is_not_active(self):
        controller = AmbientEffectController()
        state = controller.start(AmbientEffect.NONE)

        self.assertEqual(state.phase, AmbientPhase.IDLE)
        self.assertFalse(state.active)

    def test_wave_is_deterministic_and_triangular(self):
        controller = AmbientEffectController()

        self.assertEqual(controller.wave(0.0), 0.0)
        self.assertEqual(controller.wave(0.5), 1.0)
        self.assertEqual(controller.wave(1.0), 0.0)
        self.assertEqual(
            controller.wave(0.25, minimum=0.2, maximum=0.6),
            0.4,
        )


if __name__ == "__main__":
    unittest.main()
