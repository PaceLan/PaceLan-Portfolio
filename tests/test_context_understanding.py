from pathlib import Path
import tempfile
import unittest

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


class ContextUnderstandingTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        self._write(
            "target.py",
            """
class TargetClass:
    pass


def target_function():
    return 1
""",
        )

        self._write(
            "helper.py",
            """
def helper_function():
    return 2
""",
        )

        self._write(
            "consumer.py",
            """
from target import target_function


def consume():
    return target_function()
""",
        )

        self._write(
            "unrelated.py",
            """
def unrelated():
    return 99
""",
        )

        scanner = ProjectScanner(self.root)
        scan_result = scanner.scan()

        context = ProjectContextBuilder().build(scan_result)

        self.interface = ProjectContextAgentInterface(context)
        self.understanding = ContextUnderstanding(
            self.interface
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def _write(self, relative_path, content):
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            content,
            encoding="utf-8",
        )

    def _understand(self, description, context=""):
        task = WorkflowTask(
            task_id="task-001",
            project_id="project-001",
            description=description,
            context=context,
        )

        return self.understanding.understand(task)

    # ---------------------------------------------------------
    # M14 Group 1: Task Context / Relevant Files
    # ---------------------------------------------------------

    def test_context_does_not_modify_project(self):
        before = {
            path.relative_to(self.root): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }

        self._understand("Update target.py")

        after = {
            path.relative_to(self.root): path.read_bytes()
            for path in self.root.rglob("*")
            if path.is_file()
        }

        self.assertEqual(before, after)

    def test_duplicate_matches_are_deduplicated(self):
        result = self._understand(
            "Update target.py target.py"
        )

        self.assertEqual(
            len(result.relevant_files),
            len(set(result.relevant_files)),
        )

    def test_explicit_nested_path_is_selected(self):
        self._write(
            "src/nested.py",
            """
def nested_function():
    return 1
""",
        )

        scanner = ProjectScanner(self.root)
        scan_result = scanner.scan()

        context = ProjectContextBuilder().build(
            scan_result
        )

        interface = ProjectContextAgentInterface(
            context
        )

        understanding = ContextUnderstanding(
            interface
        )

        result = understanding.understand(
            WorkflowTask(
                task_id="task-002",
                project_id="project-001",
                description="Update file: src/nested.py",
            )
        )

        self.assertIn(
            Path("src/nested.py"),
            result.relevant_files,
        )

    def test_filename_match_is_selected(self):
        result = self._understand(
            "Please update target.py"
        )

        self.assertIn(
            Path("target.py"),
            result.relevant_files,
        )

    def test_invalid_interface_is_rejected(self):
        with self.assertRaises(TypeError):
            ContextUnderstanding(object())

    def test_invalid_task_is_rejected(self):
        with self.assertRaises(TypeError):
            self.understanding.understand(object())

    def test_python_module_match_is_selected(self):
        result = self._understand(
            "Please update target module"
        )

        self.assertIn(
            Path("target.py"),
            result.relevant_files,
        )

    def test_selection_is_stable(self):
        first = self._understand(
            "Update target.py helper.py"
        )

        second = self._understand(
            "Update target.py helper.py"
        )

        self.assertEqual(
            first.relevant_files,
            second.relevant_files,
        )

        self.assertEqual(
            first.relevant_files,
            tuple(
                sorted(
                    first.relevant_files,
                    key=lambda path: str(path),
                )
            ),
        )

    def test_understand_returns_immutable_result(self):
        result = self._understand(
            "Update target.py"
        )

        self.assertIsInstance(
            result,
            ContextUnderstandingResult,
        )

        with self.assertRaises(Exception):
            result.relevant_files += (
                Path("x.py"),
            )

    def test_unrelated_files_are_not_selected(self):
        result = self._understand(
            "Update target.py"
        )

        self.assertIn(
            Path("target.py"),
            result.relevant_files,
        )

        self.assertNotIn(
            Path("unrelated.py"),
            result.relevant_files,
        )

    # ---------------------------------------------------------
    # M14 Group 2: Relevant Symbols
    # ---------------------------------------------------------

    def test_relevant_symbols_are_selected(self):
        result = self._understand(
            "Update target.py"
        )

        symbol_names = {
            symbol.name
            for symbol in result.relevant_symbols
        }

        self.assertIn(
            "TargetClass",
            symbol_names,
        )

        self.assertIn(
            "target_function",
            symbol_names,
        )

    def test_relevant_symbols_have_valid_metadata(self):
        result = self._understand(
            "Update target.py"
        )

        for symbol in result.relevant_symbols:
            self.assertIsInstance(
                symbol.name,
                str,
            )

            self.assertIsInstance(
                symbol.kind,
                str,
            )

            self.assertIsInstance(
                symbol.lineno,
                int,
            )

    def test_symbols_are_stable_and_deduplicated(self):
        first = self._understand(
            "Update target.py"
        )

        second = self._understand(
            "Update target.py"
        )

        self.assertEqual(
            first.relevant_symbols,
            second.relevant_symbols,
        )

        keys = [
            (
                symbol.name,
                symbol.kind,
                symbol.lineno,
            )
            for symbol in first.relevant_symbols
        ]

        self.assertEqual(
            len(keys),
            len(set(keys)),
        )

        self.assertEqual(
            keys,
            sorted(keys),
        )

    # ---------------------------------------------------------
    # M14 Group 2: Relationship Expansion
    # ---------------------------------------------------------

    def test_relationships_are_expanded(self):
        result = self._understand(
            "Update target.py"
        )

        self.assertTrue(
            result.relationships,
        )

    def test_relationships_have_valid_metadata(self):
        result = self._understand(
            "Update target.py"
        )

        for relationship in result.relationships:
            self.assertIsInstance(
                relationship.source,
                str,
            )

            self.assertIsInstance(
                relationship.target,
                str,
            )

            self.assertIsInstance(
                relationship.kind,
                str,
            )

    def test_relationships_are_stable_and_deduplicated(self):
        first = self._understand(
            "Update target.py"
        )

        second = self._understand(
            "Update target.py"
        )

        self.assertEqual(
            first.relationships,
            second.relationships,
        )

        keys = [
            (
                relationship.source,
                relationship.target,
                relationship.kind,
            )
            for relationship in first.relationships
        ]

        self.assertEqual(
            len(keys),
            len(set(keys)),
        )

        self.assertEqual(
            keys,
            sorted(keys),
        )

    # ---------------------------------------------------------
    # M14 Group 2: Dependency Expansion
    # ---------------------------------------------------------

    def test_dependencies_are_expanded(self):
        result = self._understand(
            "Update consumer.py"
        )

        self.assertTrue(
            result.dependencies,
        )

    def test_dependencies_are_stable_and_deduplicated(self):
        first = self._understand(
            "Update consumer.py"
        )

        second = self._understand(
            "Update consumer.py"
        )

        self.assertEqual(
            first.dependencies,
            second.dependencies,
        )

        self.assertEqual(
            first.dependencies,
            tuple(
                sorted(
                    set(first.dependencies)
                )
            ),
        )

    # ---------------------------------------------------------
    # M14 Group 2: Complete Result
    # ---------------------------------------------------------

    def test_result_contains_complete_context_layers(self):
        result = self._understand(
            "Update target.py"
        )

        self.assertTrue(
            result.relevant_files,
        )

        self.assertTrue(
            result.relevant_symbols,
        )

        self.assertTrue(
            result.relationships,
        )

        self.assertIsInstance(
            result.dependencies,
            tuple,
        )

        self.assertTrue(
            result.summary,
        )

    def test_result_is_deterministic(self):
        results = [
            self._understand(
                "Update target.py"
            )
            for _ in range(3)
        ]

        self.assertEqual(
            results[0],
            results[1],
        )

        self.assertEqual(
            results[1],
            results[2],
        )

    def test_context_understanding_remains_read_only(self):
        before_files = tuple(
            sorted(
                path.relative_to(self.root)
                for path in self.root.rglob("*")
                if path.is_file()
            )
        )

        before_contents = {
            path: (self.root / path).read_bytes()
            for path in before_files
        }

        result = self._understand(
            "Update target.py"
        )

        after_files = tuple(
            sorted(
                path.relative_to(self.root)
                for path in self.root.rglob("*")
                if path.is_file()
            )
        )

        after_contents = {
            path: (self.root / path).read_bytes()
            for path in after_files
        }

        self.assertIsNotNone(result)

        self.assertEqual(
            before_files,
            after_files,
        )

        self.assertEqual(
            before_contents,
            after_contents,
        )


if __name__ == "__main__":
    unittest.main()