import tempfile
import unittest
from pathlib import Path

from agent_workflow.dependency_graph import DependencyGraph
from agent_workflow.file_index import FileIndex
from agent_workflow.project_context import (
    ProjectContext,
    ProjectContextBuilder,
)
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.python_ast import PythonAST
from agent_workflow.python_relationships import (
    PythonModuleRelationships,
)


class ProjectContextTests(unittest.TestCase):
    def test_build_creates_complete_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "main.py").write_text(
                "import helper\n\n"
                "class Main:\n"
                "    pass\n\n"
                "def run():\n"
                "    pass\n",
                encoding="utf-8",
            )

            (root / "helper.py").write_text(
                "def help_me():\n"
                "    pass\n",
                encoding="utf-8",
            )

            scan_result = ProjectScanner(root).scan()
            context = ProjectContextBuilder().build(scan_result)

            self.assertIsInstance(context, ProjectContext)
            self.assertEqual(context.root_path, root.resolve())
            self.assertIs(context.scan_result, scan_result)
            self.assertIsInstance(context.file_index, FileIndex)
            self.assertIsInstance(context.dependency_graph, DependencyGraph)

            self.assertEqual(
                [item.relative_path for item in context.python_asts],
                [Path("helper.py"), Path("main.py")],
            )

            self.assertTrue(
                all(
                    isinstance(item, PythonAST)
                    for item in context.python_asts
                )
            )

            self.assertTrue(
                all(
                    isinstance(item, PythonModuleRelationships)
                    for item in context.python_relationships
                )
            )

    def test_only_python_files_are_analyzed(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "main.py").write_text(
                "def run():\n"
                "    pass\n",
                encoding="utf-8",
            )

            (root / "notes.md").write_text(
                "# Notes\n",
                encoding="utf-8",
            )

            scan_result = ProjectScanner(root).scan()
            context = ProjectContextBuilder().build(scan_result)

            self.assertEqual(len(context.python_asts), 1)
            self.assertEqual(
                context.python_asts[0].relative_path,
                Path("main.py"),
            )

    def test_python_relationships_feed_dependency_graph(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "main.py").write_text(
                "import helper\n",
                encoding="utf-8",
            )

            (root / "helper.py").write_text(
                "def run():\n"
                "    pass\n",
                encoding="utf-8",
            )

            scan_result = ProjectScanner(root).scan()
            context = ProjectContextBuilder().build(scan_result)

            self.assertEqual(
                context.dependency_graph.nodes,
                (
                    Path("helper.py"),
                    Path("main.py"),
                ),
            )

            self.assertEqual(
                len(context.dependency_graph.edges),
                1,
            )

            edge = context.dependency_graph.edges[0]

            self.assertEqual(edge.source, Path("main.py"))
            self.assertEqual(edge.target, "helper")

    def test_context_is_immutable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "main.py").write_text(
                "def run():\n"
                "    pass\n",
                encoding="utf-8",
            )

            scan_result = ProjectScanner(root).scan()
            context = ProjectContextBuilder().build(scan_result)

            with self.assertRaises(AttributeError):
                context.root_path = root

    def test_empty_python_project_builds_context(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "README.md").write_text(
                "# Project\n",
                encoding="utf-8",
            )

            scan_result = ProjectScanner(root).scan()
            context = ProjectContextBuilder().build(scan_result)

            self.assertEqual(context.python_asts, ())
            self.assertEqual(context.python_relationships, ())
            self.assertEqual(context.dependency_graph.nodes, ())
            self.assertEqual(context.dependency_graph.edges, ())


if __name__ == "__main__":
    unittest.main()
