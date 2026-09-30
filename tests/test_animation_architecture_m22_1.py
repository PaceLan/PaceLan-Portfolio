import unittest

from ui.animation import (
    AnimationController,
    AnimationKind,
    AnimationRequest,
    AnimationSpec,
)


class M221AnimationArchitectureTests(unittest.TestCase):
    def test_animation_spec_is_immutable_and_valid(self):
        spec = AnimationSpec(
            kind=AnimationKind.FADE,
            duration_ms=200,
            steps=10,
        )

        self.assertEqual(spec.kind, AnimationKind.FADE)
        self.assertEqual(spec.duration_ms, 200)
        self.assertEqual(spec.steps, 10)

        with self.assertRaises(Exception):
            spec.duration_ms = 300

    def test_animation_spec_rejects_invalid_values(self):
        with self.assertRaises(ValueError):
            AnimationSpec(duration_ms=-1)

        with self.assertRaises(ValueError):
            AnimationSpec(steps=0)

    def test_animation_request_requires_source_and_target(self):
        spec = AnimationSpec(kind=AnimationKind.PULSE)

        with self.assertRaises(ValueError):
            AnimationRequest("", "target", spec)

        with self.assertRaises(ValueError):
            AnimationRequest("source", "", spec)

    def test_controller_starts_animation(self):
        request = AnimationRequest(
            source="agent",
            target="execution",
            spec=AnimationSpec(
                kind=AnimationKind.PULSE,
                duration_ms=500,
                steps=5,
            ),
        )
        controller = AnimationController()

        self.assertFalse(controller.is_running)
        self.assertIsNone(controller.active)

        self.assertIs(controller.start(request), request)
        self.assertTrue(controller.is_running)
        self.assertIs(controller.active, request)

    def test_controller_stop_returns_previous_animation(self):
        request = AnimationRequest(
            source="agent",
            target="result",
            spec=AnimationSpec(kind=AnimationKind.FADE),
        )
        controller = AnimationController()
        controller.start(request)

        self.assertIs(controller.stop(), request)
        self.assertFalse(controller.is_running)
        self.assertIsNone(controller.active)

    def test_controller_reset_is_idempotent(self):
        controller = AnimationController()

        controller.reset()
        self.assertFalse(controller.is_running)

        request = AnimationRequest(
            source="workspace",
            target="selection",
            spec=AnimationSpec(kind=AnimationKind.SLIDE),
        )
        controller.start(request)
        controller.reset()
        controller.reset()

        self.assertFalse(controller.is_running)
        self.assertIsNone(controller.active)


if __name__ == "__main__":
    unittest.main()
