import tempfile
import unittest
from pathlib import Path

from agent_workflow.agent_project_planner import AgentProjectPlanner
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowStep


class AgentProjectPlannerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)

        (self.root / "main.py").write_text(
            "print('test')\n",
            encoding="utf-8",
        )
        (self.root / "helper.py").write_text(
            "def run():\n    return 'ok'\n",
            encoding="utf-8",
        )

        scan_result = ProjectScanner(self.root).scan()
        context = ProjectContextBuilder().build(scan_result)
        self.project_context_agent = ProjectContextAgentInterface(
            context
        )
        self.planner = AgentProjectPlanner(
            self.project_context_agent,
        )

        self.task = WorkflowTask(
            task_id="planner-test",
            description="build a project-aware plan",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_constructor_accepts_project_context_agent(self) -> None:
        self.assertIs(
            self.planner.project_context_agent,
            self.project_context_agent,
        )

    def test_constructor_rejects_invalid_agent(self) -> None:
        with self.assertRaises(TypeError):
            AgentProjectPlanner(object())

    def test_build_returns_workflow_plan(self) -> None:
        plan = self.planner.build(
            self.task,
            (
                WorkflowStep(
                    operation="inspect",
                    action=lambda: "ok",
                ),
            ),
        )

        self.assertEqual(plan.task, self.task)
        self.assertEqual(len(plan.steps), 1)
        self.assertEqual(plan.steps[0].step_id, "step-001")

    def test_build_injects_project_context(self) -> None:
        plan = self.planner.build(
            self.task,
            (
                WorkflowStep(
                    operation="inspect",
                    action=lambda: "ok",
                ),
            ),
        )

        step_context = plan.steps[0].context

        self.assertIsNotNone(step_context)
        self.assertIn("total_files=2", step_context)
        self.assertIn("python_files=2", step_context)

    def test_build_preserves_existing_step_context(self) -> None:
        plan = self.planner.build(
            self.task,
            (
                WorkflowStep(
                    operation="inspect",
                    action=lambda: "ok",
                    context="existing context",
                ),
            ),
        )

        self.assertIn(
            "existing context",
            plan.steps[0].context,
        )
        self.assertIn(
            "python_files=2",
            plan.steps[0].context,
        )

    def test_build_does_not_execute_actions(self) -> None:
        executed = []

        self.planner.build(
            self.task,
            (
                WorkflowStep(
                    operation="inspect",
                    action=lambda: executed.append(True) or "ok",
                ),
            ),
        )

        self.assertEqual(executed, [])


if __name__ == "__main__":
    unittest.main()