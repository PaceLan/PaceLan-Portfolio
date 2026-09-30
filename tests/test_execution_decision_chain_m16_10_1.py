import unittest

from agent_workflow.execution_ordering import ExecutionOrdering
from agent_workflow.execution_readiness import ExecutionReadiness
from agent_workflow.step_dependency import StepDependencyAwareness
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep


class TestExecutionDecisionChainM1610(unittest.TestCase):

    def _plan(self, *step_ids):
        task = WorkflowTask(
            task_id="task-001",
            project_id="project-001",
            description="execute test workflow",
        )

        steps = tuple(
            WorkflowStep(
                operation=f"operation-{step_id}",
                action=lambda: "ok",
                step_id=step_id,
            )
            for step_id in step_ids
        )

        return WorkflowPlan(
            task=task,
            steps=steps,
        )

    def test_dependency_analysis_preserves_deterministic_order(self):
        plan = self._plan("step-001", "step-002", "step-003")

        result = StepDependencyAwareness().analyze(
            plan,
            {
                "step-002": ("step-001",),
                "step-003": ("step-002",),
            },
        )

        self.assertEqual(
            result.execution_order,
            ("step-001", "step-002", "step-003"),
        )
        self.assertEqual(result.issues, ())

    def test_execution_ordering_resolves_dependency_chain(self):
        plan = self._plan(
            "step-003",
            "step-001",
            "step-002",
        )

        ordered = ExecutionOrdering().order(
            plan,
            {
                "step-002": ("step-001",),
                "step-003": ("step-002",),
            },
        )

        self.assertEqual(
            tuple(step.step_id for step in ordered.steps),
            ("step-001", "step-002", "step-003"),
        )

    def test_dependency_cycle_is_rejected(self):
        plan = self._plan("step-001", "step-002")

        result = StepDependencyAwareness().analyze(
            plan,
            {
                "step-001": ("step-002",),
                "step-002": ("step-001",),
            },
        )

        self.assertFalse(result.execution_order == ())
        self.assertTrue(
            any(
                "dependency cycle detected" in issue
                for issue in result.issues
            )
        )

        with self.assertRaises(ValueError):
            ExecutionOrdering().order(
                plan,
                {
                    "step-001": ("step-002",),
                    "step-002": ("step-001",),
                },
            )

    def test_unknown_dependency_is_rejected(self):
        plan = self._plan("step-001")

        result = StepDependencyAwareness().analyze(
            plan,
            {
                "step-001": ("step-999",),
            },
        )

        self.assertTrue(result.issues)
        self.assertIn(
            "step-001: unknown dependency step-999",
            result.issues,
        )

        with self.assertRaises(ValueError):
            ExecutionOrdering().order(
                plan,
                {
                    "step-001": ("step-999",),
                },
            )

    def test_ordered_plan_is_execution_ready(self):
        plan = self._plan(
            "step-003",
            "step-001",
            "step-002",
        )

        ordered = ExecutionOrdering().order(
            plan,
            {
                "step-002": ("step-001",),
                "step-003": ("step-002",),
            },
        )

        readiness = ExecutionReadiness().check(ordered)

        self.assertTrue(readiness.ready)
        self.assertEqual(
            readiness.issues,
            (),
        )
        self.assertEqual(
            readiness.checked_step_ids,
            ("step-001", "step-002", "step-003"),
        )

    def test_readiness_does_not_execute_actions(self):
        calls = []

        task = WorkflowTask(
            task_id="task-001",
            project_id="project-001",
            description="readiness boundary",
        )

        def action():
            calls.append("executed")
            return "ok"

        plan = WorkflowPlan(
            task=task,
            steps=(
                WorkflowStep(
                    operation="safe-operation",
                    action=action,
                    step_id="step-001",
                ),
            ),
        )

        result = ExecutionReadiness().check(plan)

        self.assertTrue(result.ready)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
