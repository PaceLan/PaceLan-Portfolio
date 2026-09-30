"""Tests for M22.2 Agent state transition architecture."""

import unittest
from dataclasses import FrozenInstanceError, is_dataclass

from ui.agent_transitions import (
    AgentStateTransitionMapper,
    AgentTransitionRule,
    AgentVisualState,
)
from ui.animation import AnimationKind


class M222AgentStateTransitionTests(unittest.TestCase):

    def test_visual_states_are_defined(self):
        expected = {
            "idle",
            "processing",
            "understanding_ready",
            "plan_ready",
            "waiting_approval",
            "executing",
            "completed",
            "failed",
            "warning",
        }
        self.assertEqual(
            {state.value for state in AgentVisualState},
            expected,
        )

    def test_transition_rule_is_immutable(self):
        rule = AgentStateTransitionMapper.transition(
            AgentVisualState.IDLE,
            AgentVisualState.PROCESSING,
        )
        self.assertIsInstance(rule, AgentTransitionRule)
        self.assertTrue(is_dataclass(rule))

        with self.assertRaises(FrozenInstanceError):
            rule.semantic = "changed"

    def test_required_workflow_transitions_exist(self):
        required = (
            (AgentVisualState.IDLE, AgentVisualState.PROCESSING),
            (
                AgentVisualState.PROCESSING,
                AgentVisualState.UNDERSTANDING_READY,
            ),
            (
                AgentVisualState.UNDERSTANDING_READY,
                AgentVisualState.PLAN_READY,
            ),
            (
                AgentVisualState.PLAN_READY,
                AgentVisualState.WAITING_APPROVAL,
            ),
            (
                AgentVisualState.WAITING_APPROVAL,
                AgentVisualState.EXECUTING,
            ),
            (
                AgentVisualState.EXECUTING,
                AgentVisualState.COMPLETED,
            ),
        )

        for source, target in required:
            with self.subTest(source=source, target=target):
                self.assertTrue(
                    AgentStateTransitionMapper.has_transition(
                        source,
                        target,
                    )
                )

    def test_failure_transition_is_explicit(self):
        rule = AgentStateTransitionMapper.transition(
            AgentVisualState.EXECUTING,
            AgentVisualState.FAILED,
        )

        self.assertIsNotNone(rule)
        self.assertEqual(rule.semantic, "negative")

    def test_approval_transition_is_pending(self):
        rule = AgentStateTransitionMapper.transition(
            AgentVisualState.PLAN_READY,
            AgentVisualState.WAITING_APPROVAL,
        )

        self.assertIsNotNone(rule)
        self.assertEqual(rule.semantic, "pending")
        self.assertEqual(rule.animation.spec.kind, AnimationKind.PULSE)

    def test_transition_contains_animation_request(self):
        for rule in AgentStateTransitionMapper.transitions():
            with self.subTest(
                source=rule.source,
                target=rule.target,
            ):
                self.assertEqual(
                    rule.animation.source,
                    rule.source.value,
                )
                self.assertEqual(
                    rule.animation.target,
                    rule.target.value,
                )

    def test_unknown_transition_returns_none(self):
        self.assertIsNone(
            AgentStateTransitionMapper.transition(
                AgentVisualState.IDLE,
                AgentVisualState.COMPLETED,
            )
        )

    def test_transition_mapping_is_deterministic(self):
        first = AgentStateTransitionMapper.transition(
            AgentVisualState.EXECUTING,
            AgentVisualState.COMPLETED,
        )
        second = AgentStateTransitionMapper.transition(
            AgentVisualState.EXECUTING,
            AgentVisualState.COMPLETED,
        )

        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
