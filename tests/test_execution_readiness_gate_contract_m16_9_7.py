import unittest

from agent_workflow.risk_approval import (
    ExecutionReadiness,
    ExecutionReadinessGate,
)
from agent_workflow.workflow_plan import WorkflowStep
from permissions.reporting import ApprovalStatus, RiskLevel


class ExecutionReadinessGateContractM1697Tests(unittest.TestCase):

    def _step(
        self,
        step_id,
        *,
        risk=RiskLevel.SAFE,
        approval=ApprovalStatus.NOT_REQUESTED,
    ):
        return WorkflowStep(
            operation="execute",
            action=lambda: "ok",
            risk=risk,
            approval=approval,
            step_id=step_id,
        )

    def test_assess_plan_is_deterministic(self):
        steps = (
            self._step("step-001"),
            self._step(
                "step-002",
                risk=RiskLevel.HIGH_RISK,
                approval=ApprovalStatus.NOT_REQUESTED,
            ),
            self._step(
                "step-003",
                approval=ApprovalStatus.DENIED,
            ),
        )

        first = ExecutionReadinessGate.assess_plan(steps)
        second = ExecutionReadinessGate.assess_plan(steps)

        self.assertEqual(first, second)
        self.assertEqual(
            tuple(item.step_id for item in first),
            ("step-001", "step-002", "step-003"),
        )

    def test_denied_and_blocked_are_not_executable(self):
        for approval in (
            ApprovalStatus.DENIED,
            ApprovalStatus.BLOCKED,
        ):
            assessment = ExecutionReadinessGate.assess(
                self._step(
                    "step-001",
                    approval=approval,
                )
            )

            self.assertIs(
                assessment.readiness,
                ExecutionReadiness.BLOCKED,
            )
            self.assertFalse(assessment.is_ready)
            self.assertFalse(
                ExecutionReadinessGate.can_execute(
                    self._step(
                        "step-001",
                        approval=approval,
                    )
                )
            )

    def test_high_risk_requires_approval(self):
        for approval in (
            ApprovalStatus.NOT_REQUESTED,
            ApprovalStatus.DENIED,
            ApprovalStatus.BLOCKED,
        ):
            assessment = ExecutionReadinessGate.assess(
                self._step(
                    "step-001",
                    risk=RiskLevel.HIGH_RISK,
                    approval=approval,
                )
            )

            self.assertIs(
                assessment.readiness,
                ExecutionReadiness.BLOCKED,
            )

    def test_safe_not_requested_is_executable(self):
        step = self._step(
            "step-001",
            risk=RiskLevel.SAFE,
            approval=ApprovalStatus.NOT_REQUESTED,
        )

        assessment = ExecutionReadinessGate.assess(step)

        self.assertIs(
            assessment.readiness,
            ExecutionReadiness.READY,
        )
        self.assertTrue(assessment.is_ready)
        self.assertTrue(
            ExecutionReadinessGate.can_execute(step)
        )


if __name__ == "__main__":
    unittest.main()
