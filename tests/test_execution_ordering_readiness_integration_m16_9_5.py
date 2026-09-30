import unittest

from agent_workflow.execution_ordering import ExecutionOrdering
from agent_workflow.execution_readiness import (
    ExecutionReadiness,
    ExecutionReadinessResult,
)
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from permissions.reporting import ApprovalStatus, RiskLevel


class ExecutionOrderingReadinessIntegrationM1695Tests(unittest.TestCase):

    def setUp(self) -> None:
        self.task = WorkflowTask(
            task_id="task-m16-9-5",
            description="dependency ordering readiness integration",
            context="m16.9.5",
        )
        self.ordering = ExecutionOrdering()
        self.readiness = ExecutionReadiness()
        self.executed = []

    def action(self, name: str):
        def run():
            self.executed.append(name)
            return name
        return run

    def make_step(
        self,
        step_id: str,
        operation: str,
    ) -> WorkflowStep:
        return WorkflowStep(
            operation=operation,
            action=self.action(step_id),
            risk=RiskLevel.SAFE,
            approval=ApprovalStatus.NOT_REQUESTED,
            step_id=step_id,
        )

    def make_plan(self, *steps: WorkflowStep) -> WorkflowPlan:
        return WorkflowPlan(
            task=self.task,
            steps=tuple(steps),
        )

    def test_dependency_order_flows_into_readiness(self) -> None:
        plan = self.make_plan(
            self.make_step("step-003", "finalize"),
            self.make_step("step-001", "inspect"),
            self.make_step("step-002", "analyze"),
        )

        dependencies = {
            "step-002": ("step-001",),
            "step-003": ("step-002",),
        }

        ordered = self.ordering.order(
            plan,
            dependencies,
        )

        self.assertEqual(
            tuple(step.step_id for step in ordered.steps),
            ("step-001", "step-002", "step-003"),
        )

        result = self.readiness.check(ordered)

        self.assertIsInstance(result, ExecutionReadinessResult)
        self.assertTrue(result.ready)
        self.assertEqual(
            result.checked_step_ids,
            ("step-001", "step-002", "step-003"),
        )

    def test_ordering_and_readiness_are_deterministic(self) -> None:
        plan = self.make_plan(
            self.make_step("step-003", "finalize"),
            self.make_step("step-001", "inspect"),
            self.make_step("step-002", "analyze"),
        )

        dependencies = {
            "step-002": ("step-001",),
            "step-003": ("step-002",),
        }

        first = self.ordering.order(plan, dependencies)
        second = self.ordering.order(plan, dependencies)

        self.assertEqual(first, second)

        first_readiness = self.readiness.check(first)
        second_readiness = self.readiness.check(second)

        self.assertEqual(first_readiness, second_readiness)

    def test_ordering_preserves_workflow_step_objects(self) -> None:
        step1 = self.make_step("step-001", "inspect")
        step2 = self.make_step("step-002", "analyze")
        step3 = self.make_step("step-003", "finalize")

        plan = self.make_plan(step3, step1, step2)

        ordered = self.ordering.order(
            plan,
            {
                "step-002": ("step-001",),
                "step-003": ("step-002",),
            },
        )

        self.assertIs(ordered.steps[0], step1)
        self.assertIs(ordered.steps[1], step2)
        self.assertIs(ordered.steps[2], step3)

    def test_dependency_failure_blocks_ordering_before_readiness(self) -> None:
        plan = self.make_plan(
            self.make_step("step-001", "inspect"),
            self.make_step("step-002", "analyze"),
        )

        with self.assertRaises(ValueError):
            self.ordering.order(
                plan,
                {
                    "step-002": ("missing-step",),
                },
            )

    def test_dependency_cycle_blocks_ordering(self) -> None:
        plan = self.make_plan(
            self.make_step("step-001", "inspect"),
            self.make_step("step-002", "analyze"),
        )

        with self.assertRaises(ValueError):
            self.ordering.order(
                plan,
                {
                    "step-001": ("step-002",),
                    "step-002": ("step-001",),
                },
            )

    def test_empty_dependencies_preserve_original_order(self) -> None:
        plan = self.make_plan(
            self.make_step("step-003", "finalize"),
            self.make_step("step-001", "inspect"),
            self.make_step("step-002", "analyze"),
        )

        ordered = self.ordering.order(plan, {})

        self.assertEqual(
            tuple(step.step_id for step in ordered.steps),
            ("step-003", "step-001", "step-002"),
        )

        result = self.readiness.check(ordered)

        self.assertTrue(result.ready)

    def test_ordering_does_not_execute_actions(self) -> None:
        plan = self.make_plan(
            self.make_step("step-002", "analyze"),
            self.make_step("step-001", "inspect"),
        )

        self.ordering.order(
            plan,
            {
                "step-002": ("step-001",),
            },
        )

        self.assertEqual(self.executed, [])

    def test_readiness_does_not_execute_actions_after_ordering(self) -> None:
        plan = self.make_plan(
            self.make_step("step-002", "analyze"),
            self.make_step("step-001", "inspect"),
        )

        ordered = self.ordering.order(
            plan,
            {
                "step-002": ("step-001",),
            },
        )

        result = self.readiness.check(ordered)

        self.assertTrue(result.ready)
        self.assertEqual(self.executed, [])

    def test_task_identity_is_preserved_across_ordering(self) -> None:
        plan = self.make_plan(
            self.make_step("step-002", "analyze"),
            self.make_step("step-001", "inspect"),
        )

        ordered = self.ordering.order(
            plan,
            {
                "step-002": ("step-001",),
            },
        )

        self.assertIs(ordered.task, plan.task)
        self.assertEqual(ordered.task.task_id, "task-m16-9-5")


    def test_duplicate_dependency_is_rejected_before_readiness(self) -> None:
        plan = self.make_plan(
            self.make_step("step-001", "inspect"),
            self.make_step("step-002", "analyze"),
        )

        with self.assertRaises(ValueError):
            self.ordering.order(
                plan,
                {
                    "step-002": ("step-001", "step-001"),
                },
            )

    def test_self_dependency_is_rejected_before_readiness(self) -> None:
        plan = self.make_plan(
            self.make_step("step-001", "inspect"),
        )

        with self.assertRaises(ValueError):
            self.ordering.order(
                plan,
                {
                    "step-001": ("step-001",),
                },
            )

    def test_unknown_dependency_target_is_rejected(self) -> None:
        plan = self.make_plan(
            self.make_step("step-001", "inspect"),
        )

        with self.assertRaises(ValueError):
            self.ordering.order(
                plan,
                {
                    "missing-step": ("step-001",),
                },
            )

    def test_non_callable_action_is_caught_by_readiness_after_ordering(
        self,
    ) -> None:
        invalid_step = WorkflowStep(
            operation="inspect",
            action=None,
            risk=RiskLevel.SAFE,
            approval=ApprovalStatus.NOT_REQUESTED,
            step_id="step-001",
        )

        plan = self.make_plan(invalid_step)
        ordered = self.ordering.order(plan, {})
        result = self.readiness.check(ordered)

        self.assertFalse(result.ready)
        self.assertIn(
            "step-001: action must be callable",
            result.issues,
        )

    def test_invalid_risk_is_caught_by_readiness(self) -> None:
        invalid_step = WorkflowStep(
            operation="inspect",
            action=self.action("step-001"),
            risk="SAFE",
            approval=ApprovalStatus.NOT_REQUESTED,
            step_id="step-001",
        )

        plan = self.make_plan(invalid_step)
        ordered = self.ordering.order(plan, {})
        result = self.readiness.check(ordered)

        self.assertFalse(result.ready)
        self.assertIn(
            "step-001: risk must be a RiskLevel",
            result.issues,
        )

    def test_invalid_approval_is_caught_by_readiness(self) -> None:
        invalid_step = WorkflowStep(
            operation="inspect",
            action=self.action("step-001"),
            risk=RiskLevel.SAFE,
            approval="NOT_REQUESTED",
            step_id="step-001",
        )

        plan = self.make_plan(invalid_step)
        ordered = self.ordering.order(plan, {})
        result = self.readiness.check(ordered)

        self.assertFalse(result.ready)
        self.assertIn(
            "step-001: approval must be an ApprovalStatus",
            result.issues,
        )

    def test_ordering_failure_does_not_execute_any_action(self) -> None:
        plan = self.make_plan(
            self.make_step("step-001", "inspect"),
            self.make_step("step-002", "analyze"),
        )

        with self.assertRaises(ValueError):
            self.ordering.order(
                plan,
                {
                    "step-001": ("step-002",),
                    "step-002": ("step-001",),
                },
            )

        self.assertEqual(self.executed, [])

    def test_readiness_failure_does_not_execute_any_action(self) -> None:
        invalid_step = WorkflowStep(
            operation="inspect",
            action=self.action("step-001"),
            risk="INVALID",
            approval=ApprovalStatus.NOT_REQUESTED,
            step_id="step-001",
        )

        result = self.readiness.check(
            self.make_plan(invalid_step),
        )

        self.assertFalse(result.ready)
        self.assertEqual(self.executed, [])

    def test_ordered_plan_does_not_mutate_original_plan(self) -> None:
        step1 = self.make_step("step-001", "inspect")
        step2 = self.make_step("step-002", "analyze")

        plan = self.make_plan(step2, step1)
        original_steps = plan.steps

        ordered = self.ordering.order(
            plan,
            {
                "step-002": ("step-001",),
            },
        )

        self.assertIsNot(ordered, plan)
        self.assertEqual(plan.steps, original_steps)
        self.assertEqual(
            tuple(step.step_id for step in ordered.steps),
            ("step-001", "step-002"),
        )


if __name__ == "__main__":
    unittest.main()
