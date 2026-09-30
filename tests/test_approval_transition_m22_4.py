import unittest

from ui.animation import AnimationKind
from ui.approval_transition import (
    ApprovalTransitionMapper,
    ApprovalVisualState,
)


class M224ApprovalTransitionTests(unittest.TestCase):

    def test_plan_ready_can_transition_to_waiting_approval(self):
        transition = ApprovalTransitionMapper.transition(
            ApprovalVisualState.PLAN_READY,
            ApprovalVisualState.WAITING_APPROVAL,
        )

        self.assertIsNotNone(transition)
        self.assertEqual(transition.semantic, "pending")
        self.assertEqual(transition.animation.kind, AnimationKind.PULSE)

    def test_risk_detection_precedes_waiting_approval(self):
        transition = ApprovalTransitionMapper.transition(
            ApprovalVisualState.RISK_DETECTED,
            ApprovalVisualState.WAITING_APPROVAL,
        )

        self.assertIsNotNone(transition)
        self.assertEqual(transition.semantic, "pending")

    def test_waiting_approval_to_approved_is_positive(self):
        transition = ApprovalTransitionMapper.transition(
            ApprovalVisualState.WAITING_APPROVAL,
            ApprovalVisualState.APPROVED,
        )

        self.assertIsNotNone(transition)
        self.assertEqual(transition.semantic, "positive")
        self.assertEqual(transition.animation.kind, AnimationKind.FADE)

    def test_waiting_approval_to_rejected_is_negative(self):
        transition = ApprovalTransitionMapper.transition(
            ApprovalVisualState.WAITING_APPROVAL,
            ApprovalVisualState.REJECTED,
        )

        self.assertIsNotNone(transition)
        self.assertEqual(transition.semantic, "negative")

    def test_approved_to_executing_is_active(self):
        transition = ApprovalTransitionMapper.transition(
            ApprovalVisualState.APPROVED,
            ApprovalVisualState.EXECUTING,
        )

        self.assertIsNotNone(transition)
        self.assertEqual(transition.semantic, "active")
        self.assertEqual(transition.animation.kind, AnimationKind.PULSE)

    def test_unknown_transition_is_not_allowed(self):
        self.assertFalse(
            ApprovalTransitionMapper.has_transition(
                ApprovalVisualState.PLAN_READY,
                ApprovalVisualState.REJECTED,
            )
        )
        self.assertIsNone(
            ApprovalTransitionMapper.transition(
                ApprovalVisualState.PLAN_READY,
                ApprovalVisualState.REJECTED,
            )
        )

    def test_transitions_are_immutable(self):
        transition = ApprovalTransitionMapper.transition(
            ApprovalVisualState.WAITING_APPROVAL,
            ApprovalVisualState.APPROVED,
        )

        with self.assertRaises(Exception):
            transition.semantic = "negative"


if __name__ == "__main__":
    unittest.main()