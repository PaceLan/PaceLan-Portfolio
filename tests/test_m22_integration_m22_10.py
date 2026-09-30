import unittest

from ui.animation import AnimationKind, AnimationRequest, AnimationSpec
from ui.animation_accessibility import MotionMode, MotionPolicy, PerformanceSnapshot
from ui.m22_integration import M22IntegrationGate, M22IntegrationState


class M2210IntegrationGateTests(unittest.TestCase):
    def _request(self):
        return AnimationRequest(
            source="idle",
            target="running",
            spec=AnimationSpec(
                kind=AnimationKind.FADE,
                duration_ms=180,
                steps=12,
            ),
        )

    def test_initial_gate_state_is_idle(self):
        gate = M22IntegrationGate()

        self.assertIsInstance(gate.state, M22IntegrationState)
        self.assertFalse(gate.state.running)
        self.assertFalse(gate.state.reduced_motion)

    def test_gate_starts_animation(self):
        gate = M22IntegrationGate()

        state = gate.start(
            channel="agent",
            source="idle",
            target="running",
            request=self._request(),
        )

        self.assertTrue(state.running)
        self.assertEqual(state.channel, "agent")
        self.assertEqual(state.animation.source, "idle")
        self.assertEqual(state.animation.target, "running")

    def test_gate_applies_reduced_motion(self):
        gate = M22IntegrationGate(
            accessibility=__import__(
                "ui.animation_accessibility",
                fromlist=["AnimationAccessibility"],
            ).AnimationAccessibility(
                MotionPolicy(mode=MotionMode.REDUCED)
            )
        )

        state = gate.start(
            channel="agent",
            source="idle",
            target="running",
            request=self._request(),
        )

        self.assertTrue(state.reduced_motion)
        self.assertEqual(state.animation.spec.kind, AnimationKind.NONE)
        self.assertEqual(state.animation.spec.duration_ms, 0)

    def test_gate_evaluates_normal_workload(self):
        gate = M22IntegrationGate()

        state = gate.evaluate_performance(
            PerformanceSnapshot(
                active_animations=1,
                history_items=20,
                workspace_operations=10,
            )
        )

        self.assertFalse(state.ambient_suppressed)

    def test_gate_suppresses_ambient_under_load(self):
        gate = M22IntegrationGate()

        state = gate.evaluate_performance(
            PerformanceSnapshot(
                active_animations=2,
                history_items=20,
                workspace_operations=10,
            )
        )

        self.assertTrue(state.ambient_suppressed)

    def test_gate_preserves_animation_while_evaluating_performance(self):
        gate = M22IntegrationGate()

        gate.start(
            channel="result",
            source="running",
            target="success",
            request=self._request(),
        )

        state = gate.evaluate_performance(
            PerformanceSnapshot(active_animations=1)
        )

        self.assertTrue(state.running)
        self.assertEqual(state.channel, "result")

    def test_stop_clears_animation(self):
        gate = M22IntegrationGate()

        gate.start(
            channel="panel",
            source="a",
            target="b",
            request=self._request(),
        )

        state = gate.stop()

        self.assertFalse(state.running)
        self.assertIsNone(state.channel)

    def test_reset_returns_gate_to_initial_state(self):
        gate = M22IntegrationGate()

        gate.start(
            channel="workspace",
            source="a",
            target="b",
            request=self._request(),
        )

        state = gate.reset()

        self.assertFalse(state.running)
        self.assertIsNone(state.animation)
        self.assertIsNone(state.channel)


if __name__ == "__main__":
    unittest.main()
