import unittest

from agent_workflow.plan_builder import build_plan, validate_plan
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from permissions.reporting import ApprovalStatus, RiskLevel


class PlanBuilderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.task = WorkflowTask(
            "builder-task-1",
            "build a structured plan",
            "builder test context",
        )

    def test_build_plan_creates_workflow_plan(self) -> None:
        steps = (
            WorkflowStep("first", lambda: "first"),
            WorkflowStep("second", lambda: "second"),
        )

        plan = build_plan(self.task, steps)

        self.assertIsInstance(plan, WorkflowPlan)
        self.assertIs(plan.task, self.task)
        self.assertEqual(plan.steps, steps)

    def test_build_plan_accepts_iterable_and_freezes_steps(self) -> None:
        steps = [
            WorkflowStep("first", lambda: "first"),
            WorkflowStep("second", lambda: "second"),
        ]

        plan = build_plan(self.task, steps)

        self.assertIsInstance(plan.steps, tuple)
        self.assertEqual(len(plan.steps), 2)

    def test_build_plan_does_not_execute_actions(self) -> None:
        executed = []

        steps = (
            WorkflowStep(
                "must not execute",
                lambda: executed.append(True) or "executed",
            ),
        )

        plan = build_plan(self.task, steps)

        self.assertEqual(executed, [])
        self.assertEqual(plan.steps, steps)

    def test_build_plan_preserves_risk_approval_target_and_context(self) -> None:
        step = WorkflowStep(
            "reviewable operation",
            lambda: "result",
            risk=RiskLevel.NOTABLE,
            approval=ApprovalStatus.APPROVED,
            target="src/example.py",
            context="builder context",
        )

        plan = build_plan(self.task, (step,))

        self.assertEqual(plan.steps[0].risk, RiskLevel.NOTABLE)
        self.assertEqual(plan.steps[0].approval, ApprovalStatus.APPROVED)
        self.assertEqual(plan.steps[0].target, "src/example.py")
        self.assertEqual(plan.steps[0].context, "builder context")

    def test_empty_steps_build_empty_plan(self) -> None:
        plan = build_plan(self.task)

        self.assertEqual(plan.steps, ())

    def test_invalid_task_type_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            build_plan("not a task")  # type: ignore[arg-type]

    def test_invalid_step_type_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            build_plan(self.task, ("not a workflow step",))  # type: ignore[arg-type]

    def test_validate_plan_accepts_valid_plan(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (WorkflowStep("valid operation", lambda: "ok"),),
        )

        self.assertIs(validate_plan(plan), plan)

    def test_validate_plan_does_not_execute_actions(self) -> None:
        executed = []

        plan = WorkflowPlan(
            self.task,
            (
                WorkflowStep(
                    "validation only",
                    lambda: executed.append(True) or "should not execute",
                ),
            ),
        )

        validate_plan(plan)

        self.assertEqual(executed, [])

    def test_validate_plan_rejects_invalid_type(self) -> None:
        with self.assertRaises(TypeError):
            validate_plan("not a plan")  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
