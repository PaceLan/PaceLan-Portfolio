import unittest

from agent_workflow.risk_approval import (
    ExecutionReadiness,
    ExecutionReadinessGate,
)
from agent_workflow.workflow_plan import WorkflowStep
from permissions.reporting import ApprovalStatus, RiskLevel


class ExecutionReadinessGateTests(unittest.TestCase):

    def make_step(
        self,
        *,
        step_id="step-001",
        risk=RiskLevel.SAFE,
        approval=ApprovalStatus.NOT_REQUESTED,
        executed=None,
    ):
        def action():
            if executed is not None:
                executed.append(step_id)
            return "executed"

        return WorkflowStep(
            operation="test operation",
            action=action,
            risk=risk,
            approval=approval,
            step_id=step_id,
        )

    def test_safe_step_is_ready(self):
        step = self.make_step()

        assessment = ExecutionReadinessGate.assess(step)

        self.assertEqual(
            assessment.readiness,
            ExecutionReadiness.READY,
        )
        self.assertTrue(
            ExecutionReadinessGate.can_execute(step)
        )

    def test_denied_step_is_blocked(self):
        step = self.make_step(
            approval=ApprovalStatus.DENIED,
        )

        assessment = ExecutionReadinessGate.assess(step)

        self.assertEqual(
            assessment.readiness,
            ExecutionReadiness.BLOCKED,
        )
        self.assertFalse(
            ExecutionReadinessGate.can_execute(step)
        )

    def test_blocked_step_is_blocked(self):
        step = self.make_step(
            approval=ApprovalStatus.BLOCKED,
        )

        self.assertFalse(
            ExecutionReadinessGate.can_execute(step)
        )

    def test_high_risk_without_approval_is_blocked(self):
        step = self.make_step(
            risk=RiskLevel.HIGH_RISK,
            approval=ApprovalStatus.NOT_REQUESTED,
        )

        assessment = ExecutionReadinessGate.assess(step)

        self.assertEqual(
            assessment.readiness,
            ExecutionReadiness.BLOCKED,
        )
        self.assertFalse(assessment.is_ready)

    def test_high_risk_approved_is_ready(self):
        step = self.make_step(
            risk=RiskLevel.HIGH_RISK,
            approval=ApprovalStatus.APPROVED,
        )

        self.assertTrue(
            ExecutionReadinessGate.can_execute(step)
        )

    def test_gate_never_executes_action(self):
        executed = []

        step = self.make_step(
            risk=RiskLevel.HIGH_RISK,
            approval=ApprovalStatus.DENIED,
            executed=executed,
        )

        ExecutionReadinessGate.assess(step)
        ExecutionReadinessGate.can_execute(step)

        self.assertEqual(executed, [])

    def test_plan_gate_is_deterministic(self):
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

        first = ExecutionReadinessGate.assess_plan(steps)
        second = ExecutionReadinessGate.assess_plan(steps)

        self.assertEqual(first, second)
        self.assertTrue(
            ExecutionReadinessGate.is_plan_ready(steps)
        )

    def test_plan_with_blocked_step_is_not_ready(self):
        steps = (
            self.make_step(step_id="step-001"),
            self.make_step(
                step_id="step-002",
                approval=ApprovalStatus.DENIED,
            ),
        )

        self.assertFalse(
            ExecutionReadinessGate.is_plan_ready(steps)
        )

    def test_risk_and_approval_are_preserved(self):
        step = self.make_step(
            risk=RiskLevel.HIGH_RISK,
            approval=ApprovalStatus.APPROVED,
        )

        assessment = ExecutionReadinessGate.assess(step)

        self.assertEqual(
            assessment.risk,
            RiskLevel.HIGH_RISK,
        )
        self.assertEqual(
            assessment.approval,
            ApprovalStatus.APPROVED,
        )


if __name__ == "__main__":
    unittest.main()
