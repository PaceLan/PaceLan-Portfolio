import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflow.agent_project_planner import AgentProjectPlanner
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import WorkflowTask


class ProjectOperationBindingC65Tests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "main.py").write_text(
            "import helper\n\nclass Example:\n    pass\n\ndef run():\n    return 1\n",
            encoding="utf-8",
        )
        (self.root / "helper.py").write_text(
            "def help_run():\n    return True\n",
            encoding="utf-8",
        )
        (self.root / "plain.py").write_text("value = 1\n", encoding="utf-8")
        context = ProjectContextBuilder().build(ProjectScanner(self.root).scan())
        self.agent = ProjectContextAgentInterface(context)
        self.planner = AgentProjectPlanner(self.agent)

    def tearDown(self):
        self.temp.cleanup()

    def test_inspect_returns_real_file_metadata(self):
        result = self.planner._execute_project_operation("inspect", "main.py")
        self.assertIn("main.py", result)
        self.assertIn("extension=.py", result)
        self.assertIn("size=", result)

    def test_analyze_returns_ast_counts(self):
        result = self.planner._execute_project_operation("analyze", "main.py")
        self.assertIn("imports=1", result)
        self.assertIn("classes=1", result)
        self.assertIn("functions=1", result)

    def test_trace_dependencies_reports_real_imports(self):
        result = self.planner._execute_project_operation(
            "trace_dependencies", "main.py"
        )
        self.assertIn("helper", result)

    def test_trace_dependencies_distinguishes_no_dependencies(self):
        result = self.planner._execute_project_operation(
            "trace_dependencies", "plain.py"
        )
        self.assertIn("none", result)

    def test_missing_file_fails_explicitly(self):
        with self.assertRaises(FileNotFoundError):
            self.planner._execute_project_operation("inspect", "missing.py")

    def test_invalid_targets_fail_closed(self):
        for target in ("../main.py", ".", str(self.root / "main.py")):
            with self.subTest(target=target):
                with self.assertRaises(ValueError):
                    self.planner._execute_project_operation("inspect", target)

    def test_unknown_operation_fails_explicitly(self):
        with self.assertRaises(ValueError):
            self.planner._execute_project_operation("delete", "main.py")

    def test_planning_does_not_execute_project_operations(self):
        task = WorkflowTask(
            task_id="c65-planning-no-side-effects",
            description="Inspect main.py",
            context="target: main.py",
        )
        with patch.object(
            self.planner,
            "_execute_project_operation",
            wraps=self.planner._execute_project_operation,
        ) as execute:
            plan = self.planner.build(task)
            self.assertTrue(plan.steps)
            execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
