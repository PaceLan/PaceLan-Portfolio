import tempfile
import unittest
from pathlib import Path

from agent_workflow.context_understanding import ContextUnderstanding
from agent_workflow.dependency_intelligence import DependencyIntelligence
from agent_workflow.planner_intelligence import PlannerIntelligence
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import WorkflowTask


class TestDependencyIntelligencePlannerM1694(unittest.TestCase):

    def _build_context(self, files):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name)

        for relative_path, content in files.items():
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")

        scan_result = ProjectScanner(root).scan()
        context = ProjectContextBuilder().build(scan_result)
        return tmp, root, context

    def test_project_context_contains_dependency_graph(self):
        tmp, root, context = self._build_context(
            {
                "main.py": "import utility\n",
                "utility.py": "VALUE = 1\n",
            }
        )
        self.addCleanup(tmp.cleanup)

        self.assertEqual(
            tuple(str(node) for node in context.dependency_graph.nodes),
            ("main.py", "utility.py"),
        )

    def test_context_understanding_expands_real_dependencies(self):
        tmp, root, context = self._build_context(
            {
                "main.py": "import utility\n",
                "utility.py": "VALUE = 1\n",
            }
        )
        self.addCleanup(tmp.cleanup)

        interface = ProjectContextAgentInterface(context)
        task = WorkflowTask(
            task_id="task-001",
            project_id="project-001",
            description="Update main.py",
            context="target: main.py",
        )

        result = interface.context_understanding.understand_task(task)

        self.assertEqual(
            result.relevant_files,
            (Path("main.py"),),
        )
        self.assertIn("utility", result.dependencies)

    def test_dependency_intelligence_matches_real_context_graph(self):
        tmp, root, context = self._build_context(
            {
                "main.py": "import utility\n",
                "utility.py": "VALUE = 1\n",
                "consumer.py": "import main\n",
            }
        )
        self.addCleanup(tmp.cleanup)

        intelligence = DependencyIntelligence(
            context.dependency_graph
        )

        self.assertEqual(
            intelligence.dependencies_of(Path("main.py")),
            ("utility",),
        )

        impact = intelligence.impact_of(Path("main.py"))

        self.assertEqual(
            impact.direct_dependents,
            (Path("consumer.py"),),
        )
        self.assertEqual(
            impact.all_dependents,
            (Path("consumer.py"),),
        )

    def test_planner_consumes_context_dependencies_end_to_end(self):
        tmp, root, context = self._build_context(
            {
                "main.py": "import utility\n",
                "utility.py": "VALUE = 1\n",
            }
        )
        self.addCleanup(tmp.cleanup)

        interface = ProjectContextAgentInterface(context)

        task = WorkflowTask(
            task_id="task-001",
            project_id="project-001",
            description="Update main.py",
            context="target: main.py",
        )

        context_result = interface.context_understanding.understand_task(
            task
        )

        self.assertIn(
            "utility",
            context_result.dependencies,
        )

        plan = PlannerIntelligence().plan(
            task,
            context_result,
        )

        self.assertTrue(plan.steps)

        combined_context = " ".join(
            step.context or ""
            for step in plan.steps
        )

        self.assertIn(
            "utility",
            combined_context,
        )


if __name__ == "__main__":
    unittest.main()
