import unittest

from ui.animation import AnimationKind, AnimationRequest, AnimationSpec
from ui.animation_accessibility import (
    AnimationAccessibility,
    AnimationPerformanceGuard,
    MotionMode,
    MotionPolicy,
    PerformanceSnapshot,
)


class M229AnimationAccessibilityTests(unittest.TestCase):
    def test_normal_motion_preserves_animation_kind(self):
        policy = AnimationAccessibility()

        spec = policy.adapt_spec(
            AnimationSpec(
                kind=AnimationKind.FADE,
                duration_ms=180,
                steps=12,
            )
        )

        self.assertEqual(spec.kind, AnimationKind.FADE)
        self.assertEqual(spec.duration_ms, 180)
        self.assertEqual(spec.steps, 12)

    def test_reduced_motion_becomes_minimal_transition(self):
        policy = AnimationAccessibility(
            MotionPolicy(mode=MotionMode.REDUCED)
        )

        spec = policy.adapt_spec(
            AnimationSpec(
                kind=AnimationKind.SLIDE,
                duration_ms=300,
                steps=20,
            )
        )

        self.assertEqual(spec.kind, AnimationKind.NONE)
        self.assertEqual(spec.duration_ms, 0)
        self.assertEqual(spec.steps, 1)

    def test_reduced_motion_preserves_request_endpoints(self):
        policy = AnimationAccessibility(
            MotionPolicy(mode=MotionMode.REDUCED)
        )

        request = AnimationRequest(
            source="running",
            target="success",
            spec=AnimationSpec(
                kind=AnimationKind.PULSE,
                duration_ms=500,
                steps=30,
            ),
        )

        adapted = policy.adapt_request(request)

        self.assertEqual(adapted.source, "running")
        self.assertEqual(adapted.target, "success")
        self.assertEqual(adapted.spec.kind, AnimationKind.NONE)

    def test_normal_motion_caps_duration_and_steps(self):
        policy = AnimationAccessibility(
            MotionPolicy(
                max_duration_ms=200,
                max_steps=10,
            )
        )

        spec = policy.adapt_spec(
            AnimationSpec(
                kind=AnimationKind.PULSE,
                duration_ms=1000,
                steps=100,
            )
        )

        self.assertEqual(spec.duration_ms, 200)
        self.assertEqual(spec.steps, 10)

    def test_performance_guard_suppresses_concurrent_ambient_effects(self):
        guard = AnimationPerformanceGuard()

        self.assertTrue(
            guard.should_suppress_ambient(
                PerformanceSnapshot(active_animations=2)
            )
        )

    def test_performance_guard_suppresses_high_frequency_ambient_effects(self):
        guard = AnimationPerformanceGuard()

        self.assertTrue(
            guard.should_suppress_ambient(
                PerformanceSnapshot(workspace_operations=61)
            )
        )

    def test_performance_guard_handles_large_history(self):
        guard = AnimationPerformanceGuard()

        self.assertTrue(
            guard.should_suppress_ambient(
                PerformanceSnapshot(history_items=501)
            )
        )

    def test_performance_guard_normalizes_workload(self):
        guard = AnimationPerformanceGuard(
            max_active_animations=4,
            max_history_items=5000,
        )

        snapshot = guard.normalize(
            PerformanceSnapshot(
                active_animations=20,
                history_items=10000,
                workspace_operations=-1,
            )
        )

        self.assertEqual(snapshot.active_animations, 4)
        self.assertEqual(snapshot.history_items, 5000)
        self.assertEqual(snapshot.workspace_operations, 0)


if __name__ == "__main__":
    unittest.main()
