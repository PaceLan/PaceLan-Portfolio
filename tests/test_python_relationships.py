import unittest
from pathlib import Path

from agent_workflow.python_ast import (
    PythonAST,
    PythonClass,
    PythonFunction,
    PythonImport,
)
from agent_workflow.python_relationships import (
    PythonModuleRelationships,
    PythonRelationship,
    PythonRelationshipAnalyzer,
    PythonSymbol,
)


class PythonRelationshipAnalyzerTests(unittest.TestCase):
    def test_builds_symbols_and_relationships(self) -> None:
        ast_result = PythonAST(
            relative_path=Path("app.py"),
            imports=(
                PythonImport("os", 0),
                PythonImport("pathlib", 0),
            ),
            classes=(
                PythonClass("Example", 4),
            ),
            functions=(
                PythonFunction("run", 7),
            ),
        )

        result = PythonRelationshipAnalyzer().analyze(ast_result)

        self.assertEqual(
            result,
            PythonModuleRelationships(
                relative_path=Path("app.py"),
                symbols=(
                    PythonSymbol("Example", "class", 4),
                    PythonSymbol("run", "function", 7),
                ),
                relationships=(
                    PythonRelationship("app.py", "Example", "contains"),
                    PythonRelationship("app.py", "run", "contains"),
                    PythonRelationship("app.py", "os", "imports"),
                    PythonRelationship("app.py", "pathlib", "imports"),
                ),
            ),
        )

    def test_preserves_symbol_order(self) -> None:
        ast_result = PythonAST(
            relative_path=Path("module.py"),
            imports=(),
            classes=(
                PythonClass("First", 1),
                PythonClass("Second", 5),
            ),
            functions=(
                PythonFunction("run", 9),
                PythonFunction("stop", 13),
            ),
        )

        result = PythonRelationshipAnalyzer().analyze(ast_result)

        self.assertEqual(
            result.symbols,
            (
                PythonSymbol("First", "class", 1),
                PythonSymbol("Second", "class", 5),
                PythonSymbol("run", "function", 9),
                PythonSymbol("stop", "function", 13),
            ),
        )

    def test_preserves_import_level_information_as_ast_input(self) -> None:
        ast_result = PythonAST(
            relative_path=Path("module.py"),
            imports=(
                PythonImport("utils", 1),
                PythonImport("shared", 2),
            ),
            classes=(),
            functions=(),
        )

        result = PythonRelationshipAnalyzer().analyze(ast_result)

        self.assertEqual(
            result.relationships,
            (
                PythonRelationship("module.py", "utils", "imports"),
                PythonRelationship("module.py", "shared", "imports"),
            ),
        )

    def test_handles_empty_ast(self) -> None:
        ast_result = PythonAST(
            relative_path=Path("empty.py"),
            imports=(),
            classes=(),
            functions=(),
        )

        result = PythonRelationshipAnalyzer().analyze(ast_result)

        self.assertEqual(
            result,
            PythonModuleRelationships(
                relative_path=Path("empty.py"),
                symbols=(),
                relationships=(),
            ),
        )

    def test_result_is_immutable(self) -> None:
        ast_result = PythonAST(
            relative_path=Path("app.py"),
            imports=(),
            classes=(
                PythonClass("Example", 1),
            ),
            functions=(),
        )

        result = PythonRelationshipAnalyzer().analyze(ast_result)

        self.assertIsInstance(result, PythonModuleRelationships)
        self.assertIsInstance(result.symbols, tuple)
        self.assertIsInstance(result.relationships, tuple)

        with self.assertRaises(AttributeError):
            result.symbols = ()

    def test_analyzer_does_not_modify_ast_result(self) -> None:
        ast_result = PythonAST(
            relative_path=Path("app.py"),
            imports=(
                PythonImport("os", 0),
            ),
            classes=(
                PythonClass("Example", 1),
            ),
            functions=(
                PythonFunction("run", 5),
            ),
        )

        original = ast_result

        PythonRelationshipAnalyzer().analyze(ast_result)

        self.assertEqual(ast_result, original)


if __name__ == "__main__":
    unittest.main()