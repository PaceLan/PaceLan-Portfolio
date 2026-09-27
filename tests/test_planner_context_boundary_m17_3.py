import tempfile
import unittest
from pathlib import Path

from agent_workflow.agent_project_planner import AgentProjectPlanner
from agent_workflow.context_understanding import (
    ContextUnderstanding,
    ContextUnderstandingResult,
)
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep


class M173PlannerContextBoundaryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        (self.root / "main.py").write_text(
            "import helper\n\ndef main():\n    return helper.value()\n",
            encoding="utf-8",
        )
        (self.root / "helper.py").write_text(
            "def value():\n    return 42\n",
            encoding="utf-8",
        )

        scan_result = ProjectScanner(self.root).scan()
        project_context = ProjectContextBuilder().build(scan_result)
        self.context_agent = ProjectContextAgentInterface(project_context)

        self.context_understanding = ContextUnderstanding(
            self.context_agent
        )
        self.planner = AgentProjectPlanner(self.context_agent)

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def task(self) -> WorkflowTask:
        return WorkflowTask(
            task_id="task-m173",
            project_id="project-m173",
            description="inspect helper.py",
            context="target: helper.py",
        )

    def test_context_understanding_produces_planner_input(self) -> None:
        task = self.task()

        context = self.context_understanding.understand_task(task)

        self.assertIsInstance(context, ContextUnderstandingResult)
        self.assertEqual(context.task.task_id, task.task_id)
        self.assertEqual(context.task.project_id, task.project_id)
        self.assertEqual(context.task.description, task.description)

    def test_build_from_context_accepts_real_context_result(self) -> None:
        task = self.task()
        context = self.context_understanding.understand_task(task)

        plan = self.planner.build_from_context(
            task,
            context,
        )

        self.assertIsInstance(plan, WorkflowPlan)
        self.assertEqual(plan.task, task)
        self.assertGreaterEqual(len(plan.steps), 1)

    def test_context_reaches_planned_steps(self) -> None:
        task = self.task()
        context = self.context_understanding.understand_task(task)

        plan = self.planner.build_from_context(
            task,
            context,
        )

        self.assertTrue(
            any(
                step.context
                and (
                    str(context.relevant_files[0])
                    in step.context
                    if context.relevant_files
                    else True
                )
                for step in plan.steps
            )
        )

    def test_planner_does_not_execute_actions(self) -> None:
        task = self.task()
        context = self.context_understanding.understand_task(task)

        executed = []

        step = WorkflowStep(
            operation="inspect",
            action=lambda: executed.append("executed"),
            target="helper.py",
        )

        plan = self.planner.build_from_context(
            task,
            context,
            steps=(step,),
        )

        self.assertIsInstance(plan, WorkflowPlan)
        self.assertEqual(executed, [])

    def test_planner_preserves_task_identity(self) -> None:
        task = self.task()
        context = self.context_understanding.understand_task(task)

        plan = self.planner.build_from_context(
            task,
            context,
        )

        self.assertIs(plan.task, task)
        self.assertEqual(plan.task.task_id, task.task_id)
        self.assertEqual(plan.task.project_id, task.project_id)
        self.assertEqual(plan.task.description, task.description)

    def test_planner_normalizes_and_validates_steps(self) -> None:
        task = self.task()
        context = self.context_understanding.understand_task(task)

        plan = self.planner.build_from_context(
            task,
            context,
            steps=(
                WorkflowStep(
                    operation="inspect",
                    action=lambda: None,
                    target="helper.py",
                    step_id="",
                ),
            ),
        )

        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].step_id, "step-001")
        self.assertEqual(plan.steps[0].operation, "inspect")

    def test_invalid_context_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            self.planner.build_from_context(
                self.task(),
                object(),
            )

    def test_invalid_task_is_rejected(self) -> None:
        context = self.context_understanding.understand_task(
            self.task()
        )

        with self.assertRaises(TypeError):
            self.planner.build_from_context(
                object(),
                context,
            )


if __name__ == "__main__":
    unittest.main()
