import unittest

from agent_workflow.step_dependency import (
    StepDependencyAwareness,
    StepDependencyResult,
)
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep


class StepDependencyAwarenessTests(unittest.TestCase):

    def setUp(self) -> None:
        self.task = WorkflowTask(
            task_id="task-dependency-001",
            description="dependency test",
            context="test",
        )
        self.awareness = StepDependencyAwareness()

    def make_step(
        self,
        step_id: str,
        operation: str = "inspect",
        action=None,
    ) -> WorkflowStep:
        if action is None:
            action = lambda: "must not execute"

        return WorkflowStep(
            operation=operation,
            action=action,
            step_id=step_id,
        )

    def _plan(self, *step_ids, actions=None) -> WorkflowPlan:
        if actions is None:
            actions = [None] * len(step_ids)

        steps = tuple(
            self.make_step(
                step_id,
                operation=f"operation-{index + 1}",
                action=actions[index],
            )
            for index, step_id in enumerate(step_ids)
        )

        return WorkflowPlan(self.task, steps)

    def test_returns_structured_result(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (self.make_step("step-001"),),
        )

        result = self.awareness.analyze(plan)

        self.assertIsInstance(result, StepDependencyResult)

    def test_single_step_has_no_dependencies(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (self.make_step("step-001"),),
        )

        result = self.awareness.analyze(plan)

        self.assertEqual(
            result.dependencies,
            (("step-001", ()),),
        )

    def test_dependencies_are_reported_in_plan_order(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (
                self.make_step("step-001"),
                self.make_step("step-002", "analyze"),
                self.make_step("step-003", "trace"),
            ),
        )

        result = self.awareness.analyze(plan)

        self.assertEqual(
            result.dependencies,
            (
                ("step-001", ()),
                ("step-002", ()),
                ("step-003", ()),
            ),
        )

    def test_explicit_dependencies_are_reported(self) -> None:
        plan = self._plan(
            "step-001",
            "step-002",
            "step-003",
        )

        result = self.awareness.analyze(
            plan,
            {
                "step-002": ("step-001",),
                "step-003": ("step-001", "step-002"),
            },
        )

        self.assertEqual(
            result.dependencies,
            (
                ("step-001", ()),
                ("step-002", ("step-001",)),
                ("step-003", ("step-001", "step-002")),
            ),
        )

    def test_execution_order_matches_plan_order(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (
                self.make_step("step-001"),
                self.make_step("step-002"),
                self.make_step("step-003"),
            ),
        )

        result = self.awareness.analyze(plan)

        self.assertEqual(
            result.execution_order,
            ("step-001", "step-002", "step-003"),
        )

    def test_topological_order_respects_dependencies(self) -> None:
        plan = self._plan(
            "step-001",
            "step-002",
            "step-003",
        )

        result = self.awareness.analyze(
            plan,
            {
                "step-001": ("step-003",),
            },
        )

        self.assertEqual(
            result.execution_order,
            (
                "step-002",
                "step-003",
                "step-001",
            ),
        )

    def test_empty_plan_is_valid(self) -> None:
        plan = WorkflowPlan(self.task, ())

        result = self.awareness.analyze(plan)

        self.assertEqual(result.dependencies, ())
        self.assertEqual(result.execution_order, ())
        self.assertEqual(result.issues, ())

    def test_invalid_plan_type_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            self.awareness.analyze(None)

    def test_empty_step_id_is_reported(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (self.make_step(""),),
        )

        result = self.awareness.analyze(plan)

        self.assertIn(
            "step_id must not be empty",
            result.issues,
        )

    def test_duplicate_step_ids_are_reported(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (
                self.make_step("step-001"),
                self.make_step("step-001", "analyze"),
            ),
        )

        result = self.awareness.analyze(plan)

        self.assertIn(
            "step-001: duplicate step_id",
            result.issues,
        )

    def test_unknown_dependency_is_reported(self) -> None:
        plan = self._plan(
            "step-001",
            "step-002",
        )

        result = self.awareness.analyze(
            plan,
            {
                "step-002": ("step-999",),
            },
        )

        self.assertTrue(
            any(
                "unknown dependency" in issue
                for issue in result.issues
            )
        )

    def test_unknown_dependency_target_is_reported(self) -> None:
        plan = self._plan(
            "step-001",
            "step-002",
        )

        result = self.awareness.analyze(
            plan,
            {
                "step-999": ("step-001",),
            },
        )

        self.assertIn(
            "step-999: dependency target is unknown",
            result.issues,
        )

    def test_self_dependency_is_reported(self) -> None:
        plan = self._plan(
            "step-001",
            "step-002",
        )

        result = self.awareness.analyze(
            plan,
            {
                "step-002": ("step-002",),
            },
        )

        self.assertTrue(
            any(
                "self dependency" in issue
                for issue in result.issues
            )
        )

    def test_dependency_cycle_is_reported(self) -> None:
        plan = self._plan(
            "step-001",
            "step-002",
            "step-003",
        )

        result = self.awareness.analyze(
            plan,
            {
                "step-001": ("step-003",),
                "step-002": ("step-001",),
                "step-003": ("step-002",),
            },
        )

        self.assertTrue(
            any(
                "dependency cycle detected" in issue
                for issue in result.issues
            )
        )

    def test_duplicate_dependencies_are_reported(self) -> None:
        plan = self._plan(
            "step-001",
            "step-002",
        )

        result = self.awareness.analyze(
            plan,
            {
                "step-002": (
                    "step-001",
                    "step-001",
                ),
            },
        )

        self.assertTrue(
            any(
                "duplicate dependency" in issue
                for issue in result.issues
            )
        )

    def test_dependency_analysis_does_not_execute_actions(self) -> None:
        executed = []

        plan = self._plan(
            "step-001",
            "step-002",
            actions=(
                lambda: executed.append("one"),
                lambda: executed.append("two"),
            ),
        )

        self.awareness.analyze(
            plan,
            {
                "step-002": ("step-001",),
            },
        )

        self.assertEqual(executed, [])

    def test_analysis_never_executes_actions(self) -> None:
        executed = []

        def action() -> str:
            executed.append(True)
            return "executed"

        plan = WorkflowPlan(
            self.task,
            (
                WorkflowStep(
                    operation="inspect",
                    action=action,
                    step_id="step-001",
                ),
            ),
        )

        self.awareness.analyze(plan)

        self.assertEqual(executed, [])

    def test_dependency_analysis_does_not_mutate_plan(self) -> None:
        plan = self._plan(
            "step-001",
            "step-002",
        )
        original_steps = plan.steps

        self.awareness.analyze(
            plan,
            {
                "step-002": ("step-001",),
            },
        )

        self.assertEqual(
            plan.steps,
            original_steps,
        )

    def test_result_is_immutable(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (self.make_step("step-001"),),
        )

        result = self.awareness.analyze(plan)

        with self.assertRaises(AttributeError):
            result.execution_order = ()

    def test_analysis_is_deterministic(self) -> None:
        plan = self._plan(
            "step-001",
            "step-002",
        )

        first = self.awareness.analyze(plan)
        second = self.awareness.analyze(plan)

        self.assertEqual(first, second)

    def test_topological_order_is_deterministic(self) -> None:
        plan = self._plan(
            "step-001",
            "step-002",
            "step-003",
            "step-004",
        )

        dependencies = {
            "step-004": ("step-002",),
            "step-003": ("step-001",),
        }

        analyzer = StepDependencyAwareness()

        first = analyzer.analyze(plan, dependencies)
        second = analyzer.analyze(plan, dependencies)

        self.assertEqual(
            first.execution_order,
            second.execution_order,
        )
        self.assertEqual(
            first.execution_order,
            (
                "step-001",
                "step-002",
                "step-003",
                "step-004",
            ),
        )

    def test_invalid_dependency_target_does_not_produce_topological_order(self) -> None:
        plan = self._plan(
            "step-001",
            "step-002",
        )

        result = self.awareness.analyze(
            plan,
            {
                "step-002": ("step-999",),
            },
        )

        self.assertTrue(result.issues)
        self.assertEqual(
            result.execution_order,
            (
                "step-001",
                "step-002",
            ),
        )

    def test_cycle_falls_back_to_plan_order(self) -> None:
        plan = self._plan(
            "step-001",
            "step-002",
            "step-003",
        )

        result = self.awareness.analyze(
            plan,
            {
                "step-001": ("step-003",),
                "step-002": ("step-001",),
                "step-003": ("step-002",),
            },
        )

        self.assertEqual(
            result.execution_order,
            (
                "step-001",
                "step-002",
                "step-003",
            ),
        )


if __name__ == "__main__":
    unittest.main()
