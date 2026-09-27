import unittest

from agent_workflow.execution_ordering import ExecutionOrdering
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep


class ExecutionOrderingTests(unittest.TestCase):

    def setUp(self):
        self.task = WorkflowTask(
            "task-1",
            "ordering test",
        )

        self.actions = {
            "a": lambda: "a",
            "b": lambda: "b",
            "c": lambda: "c",
            "d": lambda: "d",
        }

    def step(self, name):
        return WorkflowStep(
            operation=name,
            action=self.actions[name],
            step_id=f"step-{name}",
        )

    def plan(self, *names):
        return WorkflowPlan(
            task=self.task,
            steps=tuple(self.step(name) for name in names),
        )

    def test_dependency_chain_is_ordered(self):
        plan = self.plan("c", "a", "b")

        ordered = ExecutionOrdering().order(
            plan,
            {
                "step-b": ("step-a",),
                "step-c": ("step-b",),
            },
        )

        self.assertEqual(
            tuple(step.step_id for step in ordered.steps),
            ("step-a", "step-b", "step-c"),
        )

    def test_independent_steps_preserve_original_order(self):
        plan = self.plan("c", "a", "b")

        ordered = ExecutionOrdering().order(
            plan,
            {},
        )

        self.assertEqual(
            tuple(step.step_id for step in ordered.steps),
            ("step-c", "step-a", "step-b"),
        )

    def test_dependency_step_cannot_execute_before_dependency(self):
        plan = self.plan("c", "b", "a")

        ordered = ExecutionOrdering().order(
            plan,
            {
                "step-c": ("step-b",),
                "step-b": ("step-a",),
            },
        )

        self.assertEqual(
            tuple(step.step_id for step in ordered.steps),
            ("step-a", "step-b", "step-c"),
        )

    def test_deterministic_ordering(self):
        plan = self.plan("d", "c", "b", "a")

        dependencies = {
            "step-c": ("step-a",),
            "step-d": ("step-b",),
        }

        first = ExecutionOrdering().order(
            plan,
            dependencies,
        )
        second = ExecutionOrdering().order(
            plan,
            dependencies,
        )

        self.assertEqual(
            tuple(step.step_id for step in first.steps),
            tuple(step.step_id for step in second.steps),
        )

    def test_invalid_dependency_is_rejected(self):
        plan = self.plan("a", "b")

        with self.assertRaises(ValueError):
            ExecutionOrdering().order(
                plan,
                {
                    "step-b": ("missing-step",),
                },
            )

    def test_dependency_cycle_is_rejected(self):
        plan = self.plan("a", "b")

        with self.assertRaises(ValueError):
            ExecutionOrdering().order(
                plan,
                {
                    "step-a": ("step-b",),
                    "step-b": ("step-a",),
                },
            )

    def test_invalid_plan_type_is_rejected(self):
        with self.assertRaises(TypeError):
            ExecutionOrdering().order("not-a-plan")

    def test_ordering_returns_new_plan(self):
        plan = self.plan("b", "a")

        ordered = ExecutionOrdering().order(
            plan,
            {
                "step-b": ("step-a",),
            },
        )

        self.assertIsNot(ordered, plan)
        self.assertIs(ordered.task, plan.task)

    def test_step_objects_are_preserved(self):
        plan = self.plan("b", "a")

        original = {step.step_id: step for step in plan.steps}

        ordered = ExecutionOrdering().order(
            plan,
            {
                "step-b": ("step-a",),
            },
        )

        for step in ordered.steps:
            self.assertIs(step, original[step.step_id])


if __name__ == "__main__":
    unittest.main()
