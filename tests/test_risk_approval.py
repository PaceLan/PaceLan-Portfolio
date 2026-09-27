import unittest

from agent_workflow.risk_approval import (
    ExecutionReadiness,
    RiskApprovalAwareness,
)
from agent_workflow.workflow_plan import WorkflowStep
from permissions.reporting import ApprovalStatus, RiskLevel


class RiskApprovalAwarenessTests(unittest.TestCase):

    def make_step(
        self,
        *,
        step_id="step-001",
        risk=RiskLevel.SAFE,
        approval=ApprovalStatus.NOT_REQUESTED,
    ):
        return WorkflowStep(
            operation="test operation",
            action=lambda: "must not execute",
            risk=risk,
            approval=approval,
            step_id=step_id,
        )

    def test_safe_step_is_ready(self):
        step = self.make_step()

        assessment = RiskApprovalAwareness.assess(step)

        self.assertTrue(assessment.is_ready)
        self.assertEqual(
            assessment.readiness,
            ExecutionReadiness.READY,
        )

    def test_risk_and_approval_are_preserved(self):
        step = self.make_step(
            risk=RiskLevel.NOTABLE,
            approval=ApprovalStatus.APPROVED,
        )

        assessment = RiskApprovalAwareness.assess(step)

        self.assertEqual(assessment.risk, RiskLevel.NOTABLE)
        self.assertEqual(
            assessment.approval,
            ApprovalStatus.APPROVED,
        )

    def test_denied_is_blocked(self):
        step = self.make_step(
            risk=RiskLevel.HIGH_RISK,
            approval=ApprovalStatus.DENIED,
        )

        assessment = RiskApprovalAwareness.assess(step)

        self.assertFalse(assessment.is_ready)
        self.assertEqual(
            assessment.readiness,
            ExecutionReadiness.BLOCKED,
        )

    def test_blocked_is_blocked(self):
        step = self.make_step(
            approval=ApprovalStatus.BLOCKED,
        )

        assessment = RiskApprovalAwareness.assess(step)

        self.assertFalse(assessment.is_ready)

    def test_high_risk_without_approval_is_blocked(self):
        step = self.make_step(
            risk=RiskLevel.HIGH_RISK,
            approval=ApprovalStatus.NOT_REQUESTED,
        )

        assessment = RiskApprovalAwareness.assess(step)

        self.assertFalse(assessment.is_ready)
        self.assertIn("high-risk", assessment.reason)

    def test_high_risk_approved_is_ready(self):
        step = self.make_step(
            risk=RiskLevel.HIGH_RISK,
            approval=ApprovalStatus.APPROVED,
        )

        assessment = RiskApprovalAwareness.assess(step)

        self.assertTrue(assessment.is_ready)

    def test_assessment_never_executes_action(self):
        executed = []

        step = WorkflowStep(
            operation="non-executing assessment",
            action=lambda: executed.append(True) or "executed",
            risk=RiskLevel.HIGH_RISK,
            approval=ApprovalStatus.DENIED,
            step_id="step-001",
        )

        RiskApprovalAwareness.assess(step)

        self.assertEqual(executed, [])

    def test_plan_readiness_is_deterministic(self):
        steps = (
            self.make_step(
                step_id="step-001",
                risk=RiskLevel.SAFE,
            ),
            self.make_step(
                step_id="step-002",
                risk=RiskLevel.HIGH_RISK,
                approval=ApprovalStatus.APPROVED,
            ),
        )

        first = RiskApprovalAwareness.assess_plan(steps)
        first = RiskApprovalAwareness.assess_plan(steps)
        second = RiskApprovalAwareness.assess_plan(steps)

        self.assertEqual(first, second)
        self.assertTrue(RiskApprovalAwareness.is_plan_ready(steps))


if __name__ == "__main__":
    unittest.main()
