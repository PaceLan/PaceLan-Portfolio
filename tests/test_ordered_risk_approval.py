import unittest

from agent_workflow.execution_ordering import ExecutionOrdering
from agent_workflow.risk_approval import (
    ExecutionReadiness,
    RiskApprovalAwareness,
)
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from permissions.reporting import ApprovalStatus, RiskLevel


class OrderedRiskApprovalTests(unittest.TestCase):

    def setUp(self):
        self.task = WorkflowTask(
            task_id="task-m16-4",
            description="risk approval ordering test",
        )

    def make_step(
        self,
        step_id,
        operation,
        *,
        risk=RiskLevel.SAFE,
        approval=ApprovalStatus.NOT_REQUESTED,
        depends_on=(),
    ):
        return WorkflowStep(
            operation=operation,
            action=lambda: "must not execute",
            risk=risk,
            approval=approval,
            step_id=step_id,
        )

    def test_ordering_preserves_risk_and_approval(self):
        steps = (
            self.make_step(
                "step-003",
                "high risk",
                risk=RiskLevel.HIGH_RISK,
                approval=ApprovalStatus.APPROVED,
            ),
            self.make_step(
                "step-001",
                "safe",
            ),
            self.make_step(
                "step-002",
                "denied",
                risk=RiskLevel.HIGH_RISK,
                approval=ApprovalStatus.DENIED,
            ),
        )

        plan = WorkflowPlan(self.task, steps)
        ordered = ExecutionOrdering().order(plan)

        original = {
            step.step_id: (step.risk, step.approval)
            for step in plan.steps
        }
        reordered = {
            step.step_id: (step.risk, step.approval)
            for step in ordered.steps
        }

        self.assertEqual(original, reordered)

    def test_ordered_plan_keeps_blocked_step_blocked(self):
        steps = (
            self.make_step(
                "step-002",
                "blocked",
                risk=RiskLevel.HIGH_RISK,
                approval=ApprovalStatus.BLOCKED,
            ),
            self.make_step(
                "step-001",
                "safe",
            ),
        )

        ordered = ExecutionOrdering().order(WorkflowPlan(self.task, steps))

        assessment = RiskApprovalAwareness.assess(
            next(
                step
                for step in ordered.steps
                if step.step_id == "step-002"
            )
        )

        self.assertEqual(
            assessment.readiness,
            ExecutionReadiness.BLOCKED,
        )

    def test_ordered_plan_keeps_high_risk_approval_requirement(self):
        steps = (
            self.make_step(
                "step-002",
                "high risk pending",
                risk=RiskLevel.HIGH_RISK,
                approval=ApprovalStatus.NOT_REQUESTED,
            ),
            self.make_step(
                "step-001",
                "safe",
            ),
        )

        ordered = ExecutionOrdering().order(WorkflowPlan(self.task, steps))

        high_risk_step = next(
            step
            for step in ordered.steps
            if step.step_id == "step-002"
        )

        assessment = RiskApprovalAwareness.assess(high_risk_step)

        self.assertFalse(assessment.is_ready)
        self.assertEqual(
            assessment.risk,
            RiskLevel.HIGH_RISK,
        )
        self.assertEqual(
            assessment.approval,
            ApprovalStatus.NOT_REQUESTED,
        )

    def test_ordering_does_not_execute_actions(self):
        executed = []

        steps = (
            WorkflowStep(
                operation="first",
                action=lambda: executed.append("first"),
                step_id="step-002",
            ),
            WorkflowStep(
                operation="second",
                action=lambda: executed.append("second"),
                step_id="step-001",
            ),
        )

        ordered = ExecutionOrdering().order(WorkflowPlan(self.task, steps))

        RiskApprovalAwareness.assess_plan(ordered.steps)

        self.assertEqual(executed, [])

    def test_original_plan_remains_unchanged(self):
        steps = (
            self.make_step(
                "step-002",
                "second",
                risk=RiskLevel.HIGH_RISK,
                approval=ApprovalStatus.APPROVED,
            ),
            self.make_step(
                "step-001",
                "first",
            ),
        )

        plan = WorkflowPlan(self.task, steps)
        original_steps = plan.steps

        ordered = ExecutionOrdering().order(plan)

        self.assertIsNot(ordered, plan)
        self.assertEqual(plan.steps, original_steps)


if __name__ == "__main__":
    unittest.main()
