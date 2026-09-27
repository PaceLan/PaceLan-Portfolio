"""Tests for deterministic planner intelligence."""

import tempfile
import unittest
from pathlib import Path

from agent_workflow.context_understanding import (
    ContextUnderstanding,
    ContextUnderstandingResult,
)
from agent_workflow.planner_intelligence import PlannerIntelligence
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.project_context_query import ProjectContextQuery
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep


class PlannerIntelligenceM152Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        (self.root / "main.py").write_text(
            "from helper import value\n",
            encoding="utf-8",
        )
        (self.root / "helper.py").write_text(
            "value = 42\n",
            encoding="utf-8",
        )
        (self.root / "unrelated.py").write_text(
            "other = True\n",
            encoding="utf-8",
        )

        scan_result = ProjectScanner(self.root).scan()
        context = ProjectContextBuilder().build(scan_result)
        interface = ProjectContextAgentInterface(context)

        self.context_understanding = ContextUnderstanding(
            interface,
        )

        self.task = WorkflowTask(
            task_id="task-001",
            project_id="project-001",
            description="inspect helper.py",
        )

        self.context = self.context_understanding.understand(
            self.task,
        )

        self.planner = PlannerIntelligence()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_plan_returns_workflow_plan(self):
        plan = self.planner.plan(
            self.task,
            self.context,
        )

        self.assertIsInstance(
            plan,
            WorkflowPlan,
        )

    def test_plan_preserves_task_identity(self):
        plan = self.planner.plan(
            self.task,
            self.context,
        )

        self.assertIs(
            plan.task,
            self.task,
        )

    def test_plan_generates_relevant_targets(self):
        plan = self.planner.plan(
            self.task,
            self.context,
        )

        targets = tuple(
            step.target
            for step in plan.steps
            if step.target is not None
        )

        self.assertIn(
            "helper.py",
            targets,
        )

    def test_targets_are_deterministically_sorted(self):
        context = ContextUnderstandingResult(
            task=self.context.task,
            relevant_files=(
                Path("zeta.py"),
                Path("alpha.py"),
                Path("beta.py"),
            ),
            relevant_symbols=self.context.relevant_symbols,
            relationships=self.context.relationships,
            dependencies=self.context.dependencies,
            summary=self.context.summary,
        )

        plan = self.planner.plan(
            self.task,
            context,
        )

        targets = tuple(
            step.target
            for step in plan.steps
            if step.target is not None
        )

        self.assertEqual(
            targets,
            (
                "alpha.py",
                "beta.py",
                "zeta.py",
            ),
        )

    def test_unrelated_file_is_not_used_as_target(self):
        plan = self.planner.plan(
            self.task,
            self.context,
        )

        targets = tuple(
            step.target
            for step in plan.steps
            if step.target is not None
        )

        self.assertNotIn(
            "unrelated.py",
            targets,
        )

    def test_context_is_injected_into_generated_steps(self):
        plan = self.planner.plan(
            self.task,
            self.context,
        )

        self.assertGreater(
            len(plan.steps),
            0,
        )

        for step in plan.steps:
            self.assertIsNotNone(
                step.context,
            )
            self.assertIn(
                "relevant_files=",
                step.context,
            )
            self.assertIn(
                "summary=",
                step.context,
            )

    def test_existing_step_context_is_preserved(self):
        original = WorkflowStep(
            operation="inspect",
            action=lambda: None,
            target="helper.py",
            context="existing-context",
        )

        plan = self.planner.plan(
            self.task,
            self.context,
            (original,),
        )

        self.assertEqual(
            len(plan.steps),
            1,
        )

        step = plan.steps[0]

        self.assertIn(
            "existing-context",
            step.context,
        )
        self.assertIn(
            "relevant_files=",
            step.context,
        )

    def test_existing_step_properties_are_preserved(self):
        original = WorkflowStep(
            operation="modify",
            action=lambda: None,
            target="helper.py",
            context="existing-context",
        )

        plan = self.planner.plan(
            self.task,
            self.context,
            (original,),
        )

        step = plan.steps[0]

        self.assertEqual(
            step.operation,
            original.operation,
        )
        self.assertIs(
            step.action,
            original.action,
        )
        self.assertEqual(
            step.risk,
            original.risk,
        )
        self.assertEqual(
            step.approval,
            original.approval,
        )
        self.assertEqual(
            step.target,
            original.target,
        )
        self.assertEqual(
            step.step_id,
            "step-001",
        )

    def test_empty_context_is_handled_safely(self):
        empty_context = ContextUnderstandingResult(
            task=self.context.task,
            relevant_files=(),
        )

        plan = self.planner.plan(
            self.task,
            empty_context,
        )

        self.assertIsInstance(
            plan,
            WorkflowPlan,
        )

        self.assertGreaterEqual(
            len(plan.steps),
            1,
        )

        for step in plan.steps:
            self.assertEqual(
                step.operation,
                "inspect",
            )

    def test_plan_is_deterministic(self):
        first = self.planner.plan(
            self.task,
            self.context,
        )
        second = self.planner.plan(
            self.task,
            self.context,
        )

        self.assertEqual(
            first.task,
            second.task,
        )

        first_structure = tuple(
            (
                step.step_id,
                step.operation,
                step.risk,
                step.approval,
                step.target,
                step.context,
            )
            for step in first.steps
        )

        second_structure = tuple(
            (
                step.step_id,
                step.operation,
                step.risk,
                step.approval,
                step.target,
                step.context,
            )
            for step in second.steps
        )

        self.assertEqual(
            first_structure,
            second_structure,
        )

    def test_actions_are_never_executed(self):
        executed = []

        def action():
            executed.append(True)

        original = WorkflowStep(
            operation="inspect",
            action=action,
            target="helper.py",
        )

        self.planner.plan(
            self.task,
            self.context,
            (original,),
        )

        self.assertEqual(
            executed,
            [],
        )

    def test_invalid_task_is_rejected(self):
        with self.assertRaises(TypeError):
            self.planner.plan(
                object(),
                self.context,
            )

    def test_invalid_context_is_rejected(self):
        with self.assertRaises(TypeError):
            self.planner.plan(
                self.task,
                object(),
            )

    def test_invalid_step_is_rejected(self):
        with self.assertRaises(TypeError):
            self.planner.plan(
                self.task,
                self.context,
                (object(),),
            )


    def test_analysis_task_generates_analyze_steps(self):
        task = WorkflowTask(
            task_id="task-analysis",
            project_id="project-001",
            description="analyze helper.py",
        )

        context = self.context_understanding.understand(task)
        plan = self.planner.plan(task, context)

        operations = tuple(
            step.operation
            for step in plan.steps
        )

        self.assertIn("inspect", operations)
        self.assertIn("analyze", operations)

    def test_dependency_task_generates_dependency_steps(self):
        task = WorkflowTask(
            task_id="task-dependency",
            project_id="project-001",
            description="trace dependencies of helper.py",
        )

        context = self.context_understanding.understand(task)
        plan = self.planner.plan(task, context)

        operations = tuple(
            step.operation
            for step in plan.steps
        )

        self.assertIn("inspect", operations)
        self.assertIn("trace_dependencies", operations)

    def test_combined_task_generates_ordered_operations(self):
        task = WorkflowTask(
            task_id="task-combined",
            project_id="project-001",
            description="analyze helper.py and trace its dependencies",
        )

        context = self.context_understanding.understand(task)
        plan = self.planner.plan(task, context)

        operations = tuple(
            step.operation
            for step in plan.steps
        )

        self.assertIn("inspect", operations)
        self.assertIn("analyze", operations)
        self.assertIn("trace_dependencies", operations)

        dependency_index = operations.index(
            "trace_dependencies",
        )

        self.assertTrue(
            all(
                operation != "trace_dependencies"
                for operation in operations[:dependency_index]
            )
        )

    def test_analysis_task_generates_analyze_steps(self):
        task = WorkflowTask(task_id="task-analysis", project_id="project-001", description="analyze helper.py")
        context = self.context_understanding.understand(task)
        plan = self.planner.plan(task, context)
        operations = tuple(step.operation for step in plan.steps)
        self.assertIn("inspect", operations)
        self.assertIn("analyze", operations)

    def test_dependency_task_generates_dependency_steps(self):
        task = WorkflowTask(task_id="task-dependency", project_id="project-001", description="trace dependencies of helper.py")
        context = self.context_understanding.understand(task)
        plan = self.planner.plan(task, context)
        operations = tuple(step.operation for step in plan.steps)
        self.assertIn("inspect", operations)
        self.assertIn("trace_dependencies", operations)

    def test_combined_task_generates_ordered_operations(self):
        task = WorkflowTask(task_id="task-combined", project_id="project-001", description="analyze helper.py and trace its dependencies")
        context = self.context_understanding.understand(task)
        plan = self.planner.plan(task, context)
        operations = tuple(step.operation for step in plan.steps)
        self.assertIn("inspect", operations)
        self.assertIn("analyze", operations)
        self.assertIn("trace_dependencies", operations)
        self.assertLess(operations.index("inspect"), operations.index("trace_dependencies"))
        self.assertLess(operations.index("analyze"), operations.index("trace_dependencies"))

    def test_inspect_task_does_not_trigger_analysis(self):
        task = WorkflowTask(task_id="task-inspect", project_id="project-001", description="inspect helper.py")
        context = self.context_understanding.understand(task)
        plan = self.planner.plan(task, context)
        operations = tuple(step.operation for step in plan.steps)
        self.assertIn("inspect", operations)
        self.assertNotIn("analyze", operations)

    def test_dependency_trace_is_after_inspection(self):
        task = WorkflowTask(task_id="task-dependency-order", project_id="project-001", description="trace dependencies of helper.py")
        context = self.context_understanding.understand(task)
        plan = self.planner.plan(task, context)
        operations = tuple(step.operation for step in plan.steps)
        self.assertLess(operations.index("inspect"), operations.index("trace_dependencies"))

if __name__ == "__main__":
    unittest.main()
