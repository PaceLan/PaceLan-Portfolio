import tempfile
import unittest
from pathlib import Path

from agent_workflow.agent_project_planner import AgentProjectPlanner
from agent_workflow.context_understanding import ContextUnderstanding
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowStep


class AgentPlannerContextIntegrationM1682Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

        (self.root / "main.py").write_text(
            "from helper import run\n\n"
            "def main():\n"
            "    return run()\n",
            encoding="utf-8",
        )

        (self.root / "helper.py").write_text(
            "def run():\n"
            "    return 'ok'\n",
            encoding="utf-8",
        )

        (self.root / "unrelated.py").write_text(
            "def unrelated():\n"
            "    return 1\n",
            encoding="utf-8",
        )

        scan_result = ProjectScanner(self.root).scan()
        project_context = ProjectContextBuilder().build(scan_result)

        self.project_context_agent = ProjectContextAgentInterface(
            project_context
        )

        self.context_understanding = ContextUnderstanding(
            self.project_context_agent
        )

        self.planner = AgentProjectPlanner(
            self.project_context_agent
        )

        self.task = WorkflowTask(
            task_id="m16-8-2-task",
            project_id="m16-8-2-project",
            description="analyze helper.py and trace its dependencies",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_context_understanding_result_enters_build_from_context(self):
        context = self.context_understanding.understand(self.task)

        plan = self.planner.build_from_context(
            self.task,
            context,
        )

        self.assertEqual(plan.task, self.task)
        self.assertGreater(len(plan.steps), 0)

        for step in plan.steps:
            self.assertIsNotNone(step.context)
            self.assertIn("relevant_files=", step.context)
            self.assertIn("summary=", step.context)

    def test_context_relevant_file_reaches_planner_target_selection(self):
        context = self.context_understanding.understand(self.task)

        plan = self.planner.build_from_context(
            self.task,
            context,
        )

        targets = tuple(
            step.target
            for step in plan.steps
            if step.target is not None
        )

        self.assertIn("helper.py", targets)

    def test_context_data_is_injected_into_existing_steps(self):
        context = self.context_understanding.understand(self.task)

        original = WorkflowStep(
            operation="inspect",
            action=lambda: None,
            target="helper.py",
            context="pre-existing-context",
        )

        plan = self.planner.build_from_context(
            self.task,
            context,
            (original,),
        )

        self.assertEqual(len(plan.steps), 1)
        self.assertIn(
            "pre-existing-context",
            plan.steps[0].context,
        )
        self.assertIn(
            "relevant_files=",
            plan.steps[0].context,
        )
        self.assertIn(
            "summary=",
            plan.steps[0].context,
        )

    def test_build_from_context_preserves_existing_step_properties(self):
        executed = []

        original = WorkflowStep(
            operation="modify",
            action=lambda: executed.append(True),
            target="helper.py",
            context="existing-context",
        )

        plan = self.planner.build_from_context(
            self.task,
            self.context_understanding.understand(self.task),
            (original,),
        )

        step = plan.steps[0]

        self.assertEqual(step.operation, original.operation)
        self.assertIs(step.action, original.action)
        self.assertEqual(step.risk, original.risk)
        self.assertEqual(step.approval, original.approval)
        self.assertEqual(step.target, original.target)
        self.assertEqual(step.step_id, "step-001")
        self.assertEqual(executed, [])

    def test_context_drives_analysis_and_dependency_planning(self):
        context = self.context_understanding.understand(self.task)

        plan = self.planner.build_from_context(
            self.task,
            context,
        )

        operations = tuple(
            step.operation
            for step in plan.steps
        )

        self.assertIn("inspect", operations)
        self.assertIn("analyze", operations)
        self.assertIn("trace_dependencies", operations)

        inspect_index = operations.index("inspect")
        analyze_index = operations.index("analyze")
        dependency_index = operations.index("trace_dependencies")

        self.assertLess(inspect_index, analyze_index)
        self.assertLess(analyze_index, dependency_index)

    def test_task_and_project_identity_are_preserved(self):
        context = self.context_understanding.understand(self.task)

        self.assertEqual(
            context.task.task_id,
            self.task.task_id,
        )
        self.assertEqual(
            context.task.project_id,
            self.task.project_id,
        )

        plan = self.planner.build_from_context(
            self.task,
            context,
        )

        self.assertEqual(plan.task.task_id, self.task.task_id)
        self.assertEqual(
            plan.task.project_id,
            self.task.project_id,
        )

    def test_repeated_context_to_planner_is_deterministic(self):
        first_context = self.context_understanding.understand(
            self.task
        )
        second_context = self.context_understanding.understand(
            self.task
        )

        first_plan = self.planner.build_from_context(
            self.task,
            first_context,
        )
        second_plan = self.planner.build_from_context(
            self.task,
            second_context,
        )

        self.assertEqual(
            first_context,
            second_context,
        )
        self.assertEqual(
            first_plan.task,
            second_plan.task,
        )
        self.assertEqual(
            len(first_plan.steps),
            len(second_plan.steps),
        )

        for first_step, second_step in zip(
            first_plan.steps,
            second_plan.steps,
        ):
            self.assertEqual(
                first_step.step_id,
                second_step.step_id,
            )
            self.assertEqual(
                first_step.operation,
                second_step.operation,
            )
            self.assertEqual(
                first_step.risk,
                second_step.risk,
            )
            self.assertEqual(
                first_step.approval,
                second_step.approval,
            )
            self.assertEqual(
                first_step.target,
                second_step.target,
            )
            self.assertEqual(
                first_step.context,
                second_step.context,
            )

    def test_context_instances_remain_isolated_between_tasks(self):
        first_task = WorkflowTask(
            task_id="task-one",
            project_id="project-one",
            description="analyze helper.py",
        )
        second_task = WorkflowTask(
            task_id="task-two",
            project_id="project-two",
            description="inspect main.py",
        )

        first_context = self.context_understanding.understand(
            first_task
        )
        second_context = self.context_understanding.understand(
            second_task
        )

        first_plan = self.planner.build_from_context(
            first_task,
            first_context,
        )
        second_plan = self.planner.build_from_context(
            second_task,
            second_context,
        )

        self.assertEqual(first_plan.task, first_task)
        self.assertEqual(second_plan.task, second_task)

        self.assertNotEqual(
            first_plan.task.task_id,
            second_plan.task.task_id,
        )
        self.assertNotEqual(
            first_context.task.task_id,
            second_context.task.task_id,
        )


if __name__ == "__main__":
    unittest.main()