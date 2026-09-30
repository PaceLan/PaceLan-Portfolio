import tempfile
import unittest
from pathlib import Path

from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_query import ProjectContextQuery
from agent_workflow.project_scanner import ProjectScanner


class ProjectContextQueryTests(unittest.TestCase):
    def _build_context(self, root: Path):
        return ProjectContextBuilder().build(
            ProjectScanner(root).scan()
        )

    def test_rejects_invalid_context(self):
        with self.assertRaises(TypeError):
            ProjectContextQuery(None)

    def test_get_file_returns_scanned_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "main.py").write_text(
                "print('hello')\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            query = ProjectContextQuery(context)

            result = query.get_file(Path("main.py"))

            self.assertIsNotNone(result)
            self.assertEqual(
                result.relative_path,
                Path("main.py"),
            )

    def test_get_file_returns_none_for_missing_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            context = self._build_context(root)
            query = ProjectContextQuery(context)

            self.assertIsNone(
                query.get_file(Path("missing.py"))
            )

    def test_get_python_ast_returns_matching_ast(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "main.py").write_text(
                "def run():\n"
                "    pass\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            query = ProjectContextQuery(context)

            result = query.get_python_ast(Path("main.py"))

            self.assertIsNotNone(result)
            self.assertEqual(
                result.relative_path,
                Path("main.py"),
            )
            self.assertEqual(
                result.functions[0].name,
                "run",
            )

    def test_get_python_relationships_returns_matching_result(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            (root / "main.py").write_text(
                "import helper\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            query = ProjectContextQuery(context)

            result = query.get_python_relationships(
                Path("main.py")
            )

            self.assertIsNotNone(result)
            self.assertEqual(
                result.relative_path,
                Path("main.py"),
            )
            self.assertEqual(
                result.relationships[0].target,
                "helper",
            )

    def test_python_files_returns_stable_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "z.py").write_text(
                "pass\n",
                encoding="utf-8",
            )
            (root / "a.py").write_text(
                "pass\n",
                encoding="utf-8",
            )
            (root / "notes.md").write_text(
                "# Notes\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            query = ProjectContextQuery(context)

            self.assertEqual(
                query.python_files(),
                (
                    Path("a.py"),
                    Path("z.py"),
                ),
            )

    def test_dependency_targets_returns_imports(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "main.py").write_text(
                "import helper\n"
                "import utils\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            query = ProjectContextQuery(context)

            self.assertEqual(
                query.dependency_targets(Path("main.py")),
                (
                    "helper",
                    "utils",
                ),
            )

    def test_dependency_targets_returns_empty_for_unknown_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            context = self._build_context(root)
            query = ProjectContextQuery(context)

            self.assertEqual(
                query.dependency_targets(Path("missing.py")),
                (),
            )

    def test_dependents_returns_direct_dependents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "main.py").write_text(
                "import helper\n",
                encoding="utf-8",
            )
            (root / "helper.py").write_text(
                "pass\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            query = ProjectContextQuery(context)

            self.assertEqual(
                query.dependents(Path("helper.py")),
                (Path("main.py"),),
            )

    def test_dependents_returns_stable_paths(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "z.py").write_text(
                "import helper\n",
                encoding="utf-8",
            )
            (root / "a.py").write_text(
                "import helper\n",
                encoding="utf-8",
            )
            (root / "helper.py").write_text(
                "pass\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            query = ProjectContextQuery(context)

            self.assertEqual(
                query.dependents(Path("helper.py")),
                (
                    Path("a.py"),
                    Path("z.py"),
                ),
            )

    def test_dependents_returns_empty_for_unknown_file(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "main.py").write_text(
                "import helper\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            query = ProjectContextQuery(context)

            self.assertEqual(
                query.dependents(Path("missing.py")),
                (),
            )

    def test_dependency_chain_traverses_project_dependencies(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "main.py").write_text(
                "import helper\n",
                encoding="utf-8",
            )
            (root / "helper.py").write_text(
                "import utils\n",
                encoding="utf-8",
            )
            (root / "utils.py").write_text(
                "pass\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            query = ProjectContextQuery(context)

            self.assertEqual(
                query.dependency_chain(Path("main.py")),
                (
                    "helper",
                    "utils",
                ),
            )

    def test_dependency_impact_returns_recursive_dependents(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "main.py").write_text(
                "import helper\n",
                encoding="utf-8",
            )
            (root / "helper.py").write_text(
                "import utils\n",
                encoding="utf-8",
            )
            (root / "utils.py").write_text(
                "pass\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            query = ProjectContextQuery(context)

            result = query.dependency_impact(
                Path("utils.py")
            )

            self.assertEqual(
                result.target,
                Path("utils.py"),
            )
            self.assertEqual(
                result.direct_dependents,
                (Path("helper.py"),),
            )
            self.assertEqual(
                result.all_dependents,
                (
                    Path("helper.py"),
                    Path("main.py"),
                ),
            )

    def test_dependency_impact_is_immutable(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)

            (root / "main.py").write_text(
                "import helper\n",
                encoding="utf-8",
            )
            (root / "helper.py").write_text(
                "pass\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            query = ProjectContextQuery(context)

            result = query.dependency_impact(
                Path("helper.py")
            )

            with self.assertRaises(AttributeError):
                result.target = Path("other.py")

            self.assertIsInstance(
                result.direct_dependents,
                tuple,
            )
            self.assertIsInstance(
                result.all_dependents,
                tuple,
            )


if __name__ == "__main__":
    unittest.main()