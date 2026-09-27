import tempfile
import unittest
from pathlib import Path

from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
    ProjectSummary,
)
from agent_workflow.project_context_query import ProjectContextQuery
from agent_workflow.project_scanner import ProjectScanner


class ProjectContextAgentInterfaceTests(unittest.TestCase):
    def build_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "main.py").write_text(
                "import helper\n",
                encoding="utf-8",
            )
            (root / "helper.py").write_text(
                "VALUE = 1\n",
                encoding="utf-8",
            )
            (root / "notes.txt").write_text(
                "test\n",
                encoding="utf-8",
            )

            scanner = ProjectScanner(root)
            scan_result = scanner.scan()
            return ProjectContextBuilder().build(scan_result)

    def test_context_is_exposed(self):
        context = self.build_context()
        interface = ProjectContextAgentInterface(context)

        self.assertIs(interface.context, context)

    def test_query_is_exposed(self):
        context = self.build_context()
        interface = ProjectContextAgentInterface(context)

        self.assertIsInstance(interface.query, ProjectContextQuery)
        self.assertIs(interface.query.context, context)

    def test_existing_query_can_be_injected(self):
        context = self.build_context()
        query = ProjectContextQuery(context)

        interface = ProjectContextAgentInterface(
            context,
            query=query,
        )

        self.assertIs(interface.query, query)

    def test_project_summary_is_stable(self):
        context = self.build_context()
        interface = ProjectContextAgentInterface(context)

        summary = interface.project_summary

        self.assertIsInstance(summary, ProjectSummary)
        self.assertEqual(summary.root_path, context.root_path)
        self.assertEqual(summary.total_files, 3)
        self.assertEqual(summary.python_files, 2)

    def test_project_summary_is_immutable(self):
        context = self.build_context()
        interface = ProjectContextAgentInterface(context)

        with self.assertRaises(AttributeError):
            interface.project_summary.python_files = 99

    def test_rejects_invalid_context(self):
        with self.assertRaises(TypeError):
            ProjectContextAgentInterface("invalid")

    def test_rejects_invalid_query(self):
        context = self.build_context()

        with self.assertRaises(TypeError):
            ProjectContextAgentInterface(
                context,
                query="invalid",
            )


if __name__ == "__main__":
    unittest.main()