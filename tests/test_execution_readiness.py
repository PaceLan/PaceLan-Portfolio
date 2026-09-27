import unittest

from agent_workflow.execution_readiness import (
    ExecutionReadiness,
    ExecutionReadinessResult,
)
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from permissions.reporting import ApprovalStatus, RiskLevel


class ExecutionReadinessTests(unittest.TestCase):

    def setUp(self) -> None:
        self.task = WorkflowTask(
            task_id="task-readiness-001",
            description="execution readiness test",
            context="test",
        )
        self.readiness = ExecutionReadiness()

    def make_step(
        self,
        operation: str = "inspect",
        step_id: str = "step-001",
        action=None,
        risk: RiskLevel = RiskLevel.SAFE,
        approval: ApprovalStatus = ApprovalStatus.NOT_REQUESTED,
    ) -> WorkflowStep:
        if action is None:
            action = lambda: "must not execute"

        return WorkflowStep(
            operation=operation,
            action=action,
            risk=risk,
            approval=approval,
            step_id=step_id,
        )

    def test_valid_plan_is_ready(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (self.make_step(),),
        )

        result = self.readiness.check(plan)

        self.assertIsInstance(result, ExecutionReadinessResult)
        self.assertTrue(result.ready)
        self.assertEqual(result.issues, ())
        self.assertEqual(result.checked_step_ids, ("step-001",))

    def test_empty_plan_is_ready(self) -> None:
        plan = WorkflowPlan(self.task, ())

        result = self.readiness.check(plan)

        self.assertTrue(result.ready)
        self.assertEqual(result.issues, ())
        self.assertEqual(result.checked_step_ids, ())

    def test_empty_task_id_is_not_ready(self) -> None:
        task = WorkflowTask("", "invalid task")
        plan = WorkflowPlan(task, ())

        result = self.readiness.check(plan)

        self.assertFalse(result.ready)
        self.assertIn("task_id must not be empty", result.issues)

    def test_empty_step_id_is_not_ready(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (self.make_step(step_id=""),),
        )

        result = self.readiness.check(plan)

        self.assertFalse(result.ready)
        self.assertIn(
            "step-001: step_id must not be empty",
            result.issues,
        )

    def test_empty_operation_is_not_ready(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (self.make_step(operation=""),),
        )

        result = self.readiness.check(plan)

        self.assertFalse(result.ready)
        self.assertIn(
            "step-001: operation must not be empty",
            result.issues,
        )

    def test_duplicate_step_ids_are_not_ready(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (
                self.make_step("inspect", "step-001"),
                self.make_step("analyze", "step-001"),
            ),
        )

        result = self.readiness.check(plan)

        self.assertFalse(result.ready)
        self.assertIn(
            "step-001: duplicate step_id",
            result.issues,
        )

    def test_step_ids_are_reported_in_plan_order(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (
                self.make_step("inspect", "step-001"),
                self.make_step("analyze", "step-002"),
                self.make_step("trace", "step-003"),
            ),
        )

        result = self.readiness.check(plan)

        self.assertEqual(
            result.checked_step_ids,
            ("step-001", "step-002", "step-003"),
        )

    def test_denied_step_is_warning_not_structural_issue(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (
                self.make_step(
                    approval=ApprovalStatus.DENIED,
                ),
            ),
        )

        result = self.readiness.check(plan)

        self.assertTrue(result.ready)
        self.assertEqual(result.issues, ())
        self.assertEqual(len(result.warnings), 1)
        self.assertIn("approval is DENIED", result.warnings[0])

    def test_blocked_step_is_warning_not_structural_issue(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (
                self.make_step(
                    approval=ApprovalStatus.BLOCKED,
                ),
            ),
        )

        result = self.readiness.check(plan)

        self.assertTrue(result.ready)
        self.assertEqual(result.issues, ())
        self.assertEqual(len(result.warnings), 1)

    def test_readiness_never_executes_actions(self) -> None:
        executed = []

        def action() -> str:
            executed.append(True)
            return "executed"

        plan = WorkflowPlan(
            self.task,
            (
                self.make_step(action=action),
            ),
        )

        result = self.readiness.check(plan)

        self.assertTrue(result.ready)
        self.assertEqual(executed, [])

    def test_result_is_immutable(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (self.make_step(),),
        )

        result = self.readiness.check(plan)

        with self.assertRaises(AttributeError):
            result.ready = False

    def test_check_is_deterministic(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (
                self.make_step("inspect", "step-001"),
                self.make_step("analyze", "step-002"),
            ),
        )

        first = self.readiness.check(plan)
        second = self.readiness.check(plan)

        self.assertEqual(first, second)

    def test_invalid_plan_type_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            self.readiness.check(None)

    def test_non_callable_action_is_not_ready(self) -> None:
        step = WorkflowStep(
            operation="inspect",
            action=None,
            step_id="step-001",
        )
        plan = WorkflowPlan(self.task, (step,))

        result = self.readiness.check(plan)

        self.assertFalse(result.ready)
        self.assertIn(
            "step-001: action must be callable",
            result.issues,
        )


if __name__ == "__main__":
    unittest.main()
