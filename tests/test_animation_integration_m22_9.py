import unittest

from ui.animation import AnimationController, AnimationKind
from ui.animation_integration import (
    AnimationIntegration,
    AnimationIntegrationState,
)


class M229AnimationIntegrationTests(unittest.TestCase):
    def test_initial_state_is_idle(self):
        integration = AnimationIntegration()

        self.assertIsInstance(
            integration.state,
            AnimationIntegrationState,
        )
        self.assertFalse(integration.state.running)
        self.assertIsNone(integration.state.active)
        self.assertIsNone(integration.state.channel)

    def test_start_creates_active_request(self):
        integration = AnimationIntegration()

        state = integration.start(
            channel="agent",
            source="idle",
            target="running",
        )

        self.assertTrue(state.running)
        self.assertIsNotNone(state.active)
        self.assertEqual(state.channel, "agent")
        self.assertEqual(state.active.source, "idle")
        self.assertEqual(state.active.target, "running")

    def test_start_preserves_animation_spec(self):
        integration = AnimationIntegration()

        state = integration.start(
            channel="result",
            source="pending",
            target="success",
            kind=AnimationKind.PULSE,
            duration_ms=300,
            steps=20,
        )

        self.assertEqual(
            state.active.spec.kind,
            AnimationKind.PULSE,
        )
        self.assertEqual(state.active.spec.duration_ms, 300)
        self.assertEqual(state.active.spec.steps, 20)

    def test_empty_channel_is_rejected(self):
        integration = AnimationIntegration()

        with self.assertRaises(ValueError):
            integration.start(
                channel="",
                source="idle",
                target="active",
            )

    def test_integration_uses_existing_controller(self):
        controller = AnimationController()
        integration = AnimationIntegration(controller)

        integration.start(
            channel="workspace",
            source="a",
            target="b",
        )

        self.assertIsNotNone(controller.active)
        self.assertTrue(controller.is_running)

    def test_stop_clears_active_animation(self):
        integration = AnimationIntegration()

        integration.start(
            channel="agent",
            source="idle",
            target="running",
        )

        state = integration.stop()

        self.assertFalse(state.running)
        self.assertIsNone(state.active)
        self.assertIsNone(state.channel)

    def test_reset_clears_channel_and_animation(self):
        integration = AnimationIntegration()

        integration.start(
            channel="panel",
            source="workspace",
            target="agent",
        )

        state = integration.reset()

        self.assertFalse(state.running)
        self.assertIsNone(state.channel)
        self.assertIsNone(state.active)

    def test_replacing_animation_updates_channel(self):
        integration = AnimationIntegration()

        integration.start(
            channel="workspace",
            source="a",
            target="b",
        )
        state = integration.start(
            channel="agent",
            source="b",
            target="c",
            kind=AnimationKind.SLIDE,
        )

        self.assertEqual(state.channel, "agent")
        self.assertEqual(state.active.source, "b")
        self.assertEqual(state.active.target, "c")
        self.assertEqual(state.active.spec.kind, AnimationKind.SLIDE)


if __name__ == "__main__":
    unittest.main()
