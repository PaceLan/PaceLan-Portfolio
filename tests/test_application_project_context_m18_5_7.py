import tempfile
import unittest
from pathlib import Path

from agent_workflow.project_context import (
    ProjectContext,
    ProjectContextBuilder,
)
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.project_scanner import ProjectScanner


class ApplicationProjectContextM1857Tests(unittest.TestCase):
    """M18.5.7 Application -> ProjectContextAgentInterface boundary tests."""

    def _make_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "main.py").write_text(
                "import helper\n\n"
                "def run():\n"
                "    return helper.help_me()\n",
                encoding="utf-8",
            )

            (root / "helper.py").write_text(
                "def help_me():\n"
                "    return True\n",
                encoding="utf-8",
            )

            scan_result = ProjectScanner(root).scan()
            return ProjectContextBuilder().build(scan_result)

    def test_application_context_is_preserved_by_interface(self):
        context = self._make_context()

        interface = ProjectContextAgentInterface(context)

        self.assertIsInstance(context, ProjectContext)
        self.assertIs(interface.context, context)

    def test_query_is_stable_and_bound_to_context(self):
        context = self._make_context()

        interface = ProjectContextAgentInterface(context)

        self.assertIsNotNone(interface.query)
        self.assertIs(interface.query.context, context)

    def test_context_understanding_is_stable(self):
        context = self._make_context()

        interface = ProjectContextAgentInterface(context)

        understanding = interface.context_understanding

        self.assertIsNotNone(understanding)
        self.assertIs(interface.context_understanding, understanding)

    def test_project_summary_is_derived_from_context(self):
        context = self._make_context()

        interface = ProjectContextAgentInterface(context)

        summary = interface.project_summary

        self.assertEqual(summary.root_path, context.root_path)
        self.assertEqual(
            summary.total_files,
            len(context.scan_result.files),
        )
        self.assertEqual(
            summary.python_files,
            len(interface.query.python_files()),
        )

    def test_interface_does_not_replace_application_context(self):
        context = self._make_context()

        interface = ProjectContextAgentInterface(context)

        self.assertIs(interface.context, context)
        self.assertIs(interface.query.context, context)

    def test_interface_exposes_read_only_context_boundary(self):
        context = self._make_context()

        interface = ProjectContextAgentInterface(context)

        with self.assertRaises(AttributeError):
            interface.context = context

        with self.assertRaises(AttributeError):
            interface.query = interface.query

        with self.assertRaises(AttributeError):
            interface.context_understanding = interface.context_understanding

        with self.assertRaises(AttributeError):
            interface.project_summary = interface.project_summary

    def test_invalid_context_is_rejected(self):
        with self.assertRaises(TypeError):
            ProjectContextAgentInterface(object())

    def test_invalid_query_is_rejected(self):
        context = self._make_context()

        with self.assertRaises(TypeError):
            ProjectContextAgentInterface(
                context,
                query=object(),
            )


if __name__ == "__main__":
    unittest.main()