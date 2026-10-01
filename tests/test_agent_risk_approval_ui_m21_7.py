import unittest
from unittest.mock import Mock

from application.models import PlanModel, StepModel, TaskModel
from permissions.reporting import ApprovalStatus, RiskLevel
from ui.agent_adapter import AgentUIAdapter
from ui.agent_state import AgentRiskApprovalState


class M217RiskApprovalUITests(unittest.TestCase):

    def make_execution(self, steps):
        execution = Mock()
        execution.task = TaskModel(
            task_id="task-m21-7",
            project_id="project-m21-7",
            description="Risk approval UI",
        )
        execution.plan = PlanModel(
            task_id=execution.task.task_id,
            project_id=execution.task.project_id,
            steps=tuple(steps),
            ready=all(step.ready for step in steps),
        )
        execution.result.summary = "Completed"
        execution.result.status = "Success"
        execution.context_understanding = None
        return execution

    def test_default_state_contains_risk_approval(self):
        state = AgentUIAdapter.from_execution(None)

        self.assertIsInstance(
            state.risk_approval,
            AgentRiskApprovalState,
        )
        self.assertFalse(state.risk_approval.ready)
        self.assertEqual(state.risk_approval.steps, ())

    def test_safe_step_is_exposed_to_ui(self):
        execution = self.make_execution((
            StepModel(
                operation="inspect",
                step_id="step-001",
                risk=RiskLevel.SAFE,
                approval=ApprovalStatus.NOT_REQUESTED,
                readiness="READY",
                reason="risk and approval requirements satisfied",
                ready=True,
            ),
        ))

        state = AgentUIAdapter.from_execution(execution)
        assessment = state.risk_approval.steps[0]

        self.assertEqual(assessment.step_id, "step-001")
        self.assertEqual(assessment.risk, RiskLevel.SAFE.value)
        self.assertEqual(
            assessment.approval,
            ApprovalStatus.NOT_REQUESTED.value,
        )
        self.assertEqual(
            assessment.readiness,
            "READY",
        )
        self.assertTrue(assessment.ready)
        self.assertTrue(state.risk_approval.ready)

    def test_blocked_step_is_exposed_to_ui(self):
        execution = self.make_execution((
            StepModel(
                operation="delete",
                step_id="step-001",
                risk=RiskLevel.HIGH_RISK,
                approval=ApprovalStatus.DENIED,
                readiness="BLOCKED",
                reason="approval status blocks execution",
                ready=False,
            ),
        ))

        state = AgentUIAdapter.from_execution(execution)
        assessment = state.risk_approval.steps[0]

        self.assertEqual(assessment.risk, RiskLevel.HIGH_RISK.value)
        self.assertEqual(
            assessment.approval,
            ApprovalStatus.DENIED.value,
        )
        self.assertEqual(
            assessment.readiness,
            "BLOCKED",
        )
        self.assertFalse(assessment.ready)
        self.assertFalse(state.risk_approval.ready)
        self.assertIn("approval status blocks", assessment.reason)

    def test_high_risk_pending_approval_is_exposed_to_ui(self):
        execution = self.make_execution((
            StepModel(
                operation="deploy",
                step_id="step-001",
                risk=RiskLevel.HIGH_RISK,
                approval=ApprovalStatus.NOT_REQUESTED,
                readiness="BLOCKED",
                reason="high-risk step requires approval",
                ready=False,
            ),
        ))

        state = AgentUIAdapter.from_execution(execution)
        assessment = state.risk_approval.steps[0]

        self.assertEqual(
            assessment.readiness,
            "BLOCKED",
        )
        self.assertFalse(assessment.ready)
        self.assertFalse(state.risk_approval.ready)
        self.assertIn("high-risk", assessment.reason)

    def test_adapter_does_not_execute_actions(self):
        execution = self.make_execution((
            StepModel(
                operation="dangerous",
                step_id="step-001",
                risk=RiskLevel.HIGH_RISK,
                approval=ApprovalStatus.DENIED,
                readiness="BLOCKED",
                ready=False,
            ),
        ))

        state = AgentUIAdapter.from_execution(execution)

        self.assertFalse(state.risk_approval.ready)


if __name__ == "__main__":
    unittest.main()
