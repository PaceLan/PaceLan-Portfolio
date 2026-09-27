import unittest

from agent_workflow.context_understanding import (
    ContextSummary,
    ContextUnderstandingResult,
    TaskContext,
)
from agent_workflow.planner_intelligence import PlannerIntelligence
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep


class PlannerDependencyIntelligenceIntegrationTests(unittest.TestCase):

    def setUp(self) -> None:
        self.task = WorkflowTask(
            task_id="task-m16-9-4",
            project_id="project-m16-9-4",
            description="analyze dependency chain",
            context="dependency analysis",
        )

        self.context = ContextUnderstandingResult(
            task=TaskContext(
                task_id=self.task.task_id,
                project_id=self.task.project_id,
                description=self.task.description,
                context=self.task.context,
                target="",
            ),
            relevant_files=(),
            relevant_symbols=(),
            relationships=(),
            dependencies=(
                "src/core.py",
                "src/models.py",
                "src/utils.py",
            ),
            summary="dependency context",
            structured_summary=ContextSummary(
                task_id=self.task.task_id,
                project_id=self.task.project_id,
                target="",
                relevant_file_count=0,
                relevant_symbol_count=0,
                relationship_count=0,
                dependency_count=3,
            ),
        )

        self.planner = PlannerIntelligence()

    def test_dependency_context_generates_dependency_trace_step(self) -> None:
        plan = self.planner.plan(
            self.task,
            self.context,
        )

        trace_steps = tuple(
            step
            for step in plan.steps
            if step.operation == "trace_dependencies"
        )

        self.assertEqual(
            tuple(step.target for step in trace_steps),
            (
                "src/core.py",
                "src/models.py",
                "src/utils.py",
            ),
        )

    def test_dependency_targets_are_deterministic(self) -> None:
        first = self.planner.plan(
            self.task,
            self.context,
        )
        second = self.planner.plan(
            self.task,
            self.context,
        )

        self.assertEqual(
            tuple(
                (
                    step.operation,
                    step.target,
                    step.context,
                    step.step_id,
                )
                for step in first.steps
            ),
            tuple(
                (
                    step.operation,
                    step.target,
                    step.context,
                    step.step_id,
                )
                for step in second.steps
            ),
        )

    def test_dependency_targets_are_sorted(self) -> None:
        context = ContextUnderstandingResult(
            task=self.context.task,
            relevant_files=(),
            relevant_symbols=(),
            relationships=(),
            dependencies=(
                "zeta.py",
                "alpha.py",
                "middle.py",
            ),
            summary="dependency context",
        )

        plan = self.planner.plan(
            self.task,
            context,
        )

        trace_steps = tuple(
            step
            for step in plan.steps
            if step.operation == "trace_dependencies"
        )

        self.assertEqual(
            tuple(step.target for step in trace_steps),
            (
                "alpha.py",
                "middle.py",
                "zeta.py",
            ),
        )

    def test_dependency_context_is_injected_into_generated_steps(self) -> None:
        plan = self.planner.plan(
            self.task,
            self.context,
        )

        self.assertTrue(plan.steps)

        for step in plan.steps:
            self.assertIsNotNone(step.context)
            self.assertIn(
                "dependencies=('src/core.py', 'src/models.py', 'src/utils.py')",
                step.context,
            )

    def test_dependency_intent_is_required_for_dependency_trace(self) -> None:
        task = WorkflowTask(
            task_id="task-m16-9-4-no-dependency-intent",
            project_id="project-m16-9-4",
            description="inspect the project",
            context="review files",
        )

        plan = self.planner.plan(
            task,
            self.context,
        )

        self.assertFalse(
            any(
                step.operation == "trace_dependencies"
                for step in plan.steps
            )
        )

    def test_dependency_information_does_not_execute_actions(self) -> None:
        executed = []

        supplied_step = WorkflowStep(
            operation="inspect",
            action=lambda: executed.append("executed"),
            target="src/core.py",
        )

        plan = self.planner.plan(
            self.task,
            self.context,
            actions=(supplied_step,),
        )

        self.assertEqual(executed, [])
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(
            plan.steps[0].operation,
            "inspect",
        )

    def test_supplied_steps_receive_dependency_context(self) -> None:
        supplied_step = WorkflowStep(
            operation="inspect",
            action=lambda: "must not execute",
            target="src/core.py",
        )

        plan = self.planner.plan(
            self.task,
            self.context,
            actions=(supplied_step,),
        )

        self.assertEqual(len(plan.steps), 1)
        self.assertIn(
            "dependencies=('src/core.py', 'src/models.py', 'src/utils.py')",
            plan.steps[0].context,
        )

    def test_step_ids_are_normalized_deterministically(self) -> None:
        plan = self.planner.plan(
            self.task,
            self.context,
        )

        self.assertEqual(
            tuple(step.step_id for step in plan.steps),
            tuple(
                f"step-{index:03d}"
                for index in range(1, len(plan.steps) + 1)
            ),
        )

    def test_dependency_context_does_not_mutate_source_context(self) -> None:
        original = self.context.dependencies

        self.planner.plan(
            self.task,
            self.context,
        )

        self.assertEqual(
            self.context.dependencies,
            original,
        )

    def test_dependency_context_preserves_workflow_task_identity(self) -> None:
        plan = self.planner.plan(
            self.task,
            self.context,
        )

        self.assertIsInstance(plan, WorkflowPlan)
        self.assertEqual(
            plan.task.task_id,
            self.task.task_id,
        )
        self.assertEqual(
            plan.task.project_id,
            self.task.project_id,
        )


if __name__ == "__main__":
    unittest.main()
