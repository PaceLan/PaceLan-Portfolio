import tempfile
import unittest
from pathlib import Path

from agent_workflow.context_understanding import ContextUnderstanding
from agent_workflow.dependency_graph import DependencyGraphBuilder
from agent_workflow.dependency_intelligence import DependencyIntelligence
from agent_workflow.planner_intelligence import PlannerIntelligence
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import WorkflowTask


class DependencyPlannerIntegrationM1692Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)

        self.project_root = root / "project"
        self.project_root.mkdir()

        (self.project_root / "main.py").write_text(
            "from helper import run\n\nrun()\n",
            encoding="utf-8",
        )

        (self.project_root / "helper.py").write_text(
            "from utility import value\n\n"
            "def run():\n"
            "    return value()\n",
            encoding="utf-8",
        )

        (self.project_root / "utility.py").write_text(
            "def value():\n"
            "    return 'ok'\n",
            encoding="utf-8",
        )

        scan_result = ProjectScanner(self.project_root).scan()
        context = ProjectContextBuilder().build(scan_result)

        self.project_context_agent = ProjectContextAgentInterface(context)
        self.context_understanding = ContextUnderstanding(
            self.project_context_agent
        )

        self.graph = DependencyGraphBuilder().build(
            context.python_relationships,
        )
        self.intelligence = DependencyIntelligence(self.graph)
        self.planner = PlannerIntelligence()

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _task(
        self,
        description: str = "inspect dependencies",
    ) -> WorkflowTask:
        return WorkflowTask(
            task_id="task-m1692",
            project_id="project-m1692",
            description=description,
        )

    def test_dependency_intelligence_finds_direct_dependency(self) -> None:
        main = Path("main.py")

        dependencies = self.intelligence.dependencies_of(main)

        self.assertIn("helper", dependencies)

    def test_dependency_intelligence_finds_recursive_chain(self) -> None:
        main = Path("main.py")

        chain = self.intelligence.dependency_chain(main)

        self.assertIn("helper", chain)
        self.assertIn("utility", chain)

    def test_context_contains_dependency_information(self) -> None:
        task = self._task()

        understood = self.context_understanding.understand(task)

        self.assertIsNotNone(understood)
        self.assertIsInstance(
            understood.dependencies,
            tuple,
        )

    def test_dependency_intent_generates_dependency_steps(self) -> None:
        task = self._task(
            "inspect dependency imports and dependency chain"
        )

        understood = self.context_understanding.understand(task)

        plan = self.planner.plan(
            task,
            understood,
        )

        operations = tuple(
            step.operation
            for step in plan.steps
        )

        self.assertIn("inspect", operations)
        self.assertIn(
            "trace_dependencies",
            operations,
        )

    def test_dependency_planning_is_deterministic(self) -> None:
        task = self._task(
            "inspect dependencies"
        )

        understood = self.context_understanding.understand(task)

        first = self.planner.plan(
            task,
            understood,
        )
        second = self.planner.plan(
            task,
            understood,
        )

        self.assertEqual(
            first.task,
            second.task,
        )

        self.assertEqual(
            tuple(
                (
                    step.step_id,
                    step.operation,
                    step.target,
                    step.context,
                    step.risk,
                    step.approval,
                )
                for step in first.steps
            ),
            tuple(
                (
                    step.step_id,
                    step.operation,
                    step.target,
                    step.context,
                    step.risk,
                    step.approval,
                )
                for step in second.steps
            ),
        )

    def test_dependency_planning_preserves_task_identity(self) -> None:
        task = self._task(
            "trace dependency chain"
        )

        understood = self.context_understanding.understand(task)
        plan = self.planner.plan(
            task,
            understood,
        )

        self.assertEqual(
            plan.task.task_id,
            task.task_id,
        )
        self.assertEqual(
            plan.task.project_id,
            task.project_id,
        )


if __name__ == "__main__":
    unittest.main()