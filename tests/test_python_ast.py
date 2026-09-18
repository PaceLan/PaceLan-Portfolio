import tempfile
import unittest
from pathlib import Path

from agent_workflow.python_ast import (
    PythonAST,
    PythonASTAnalyzer,
    PythonClass,
    PythonFunction,
    PythonImport,
)


class PythonASTAnalyzerTests(unittest.TestCase):
    def test_analyzes_imports_classes_and_functions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            source_path = project_path / "app.py"

            source_path.write_text(
                "import os\n"
                "from pathlib import Path\n"
                "\n"
                "class Example:\n"
                "    pass\n"
                "\n"
                "def run():\n"
                "    return 1\n",
                encoding="utf-8",
            )

            result = PythonASTAnalyzer().analyze(
                source_path,
                Path("app.py"),
            )

            self.assertEqual(
                result,
                PythonAST(
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
                ),
            )

    def test_analyzes_async_functions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            source_path = Path(temporary_root) / "async_app.py"

            source_path.write_text(
                "async def fetch():\n"
                "    return None\n",
                encoding="utf-8",
            )

            result = PythonASTAnalyzer().analyze(source_path)

            self.assertEqual(
                result.functions,
                (
                    PythonFunction("fetch", 1),
                ),
            )

    def test_records_relative_import_level(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            source_path = Path(temporary_root) / "module.py"

            source_path.write_text(
                "from .utils import helper\n"
                "from ..shared import value\n",
                encoding="utf-8",
            )

            result = PythonASTAnalyzer().analyze(source_path)

            self.assertEqual(
                result.imports,
                (
                    PythonImport("utils", 1),
                    PythonImport("shared", 2),
                ),
            )

    def test_ignores_nested_classes_and_functions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            source_path = Path(temporary_root) / "nested.py"

            source_path.write_text(
                "class Outer:\n"
                "    class Inner:\n"
                "        pass\n"
                "\n"
                "    def method(self):\n"
                "        return None\n"
                "\n"
                "def outer_function():\n"
                "    def inner_function():\n"
                "        return None\n"
                "    return inner_function\n",
                encoding="utf-8",
            )

            result = PythonASTAnalyzer().analyze(source_path)

            self.assertEqual(
                result.classes,
                (
                    PythonClass("Outer", 1),
                ),
            )
            self.assertEqual(
                result.functions,
                (
                    PythonFunction("outer_function", 8),
                ),
            )

    def test_result_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            source_path = Path(temporary_root) / "app.py"
            source_path.write_text(
                "def run():\n"
                "    pass\n",
                encoding="utf-8",
            )

            result = PythonASTAnalyzer().analyze(source_path)

            self.assertIsInstance(result, PythonAST)
            self.assertIsInstance(result.imports, tuple)
            self.assertIsInstance(result.classes, tuple)
            self.assertIsInstance(result.functions, tuple)

            with self.assertRaises(AttributeError):
                result.functions = ()

    def test_does_not_execute_source_code(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            source_path = Path(temporary_root) / "unsafe.py"
            marker_path = Path(temporary_root) / "marker.txt"

            source_path.write_text(
                "marker = open('marker.txt', 'w', encoding='utf-8')\n"
                "marker.write('executed')\n"
                "marker.close()\n",
                encoding="utf-8",
            )

            PythonASTAnalyzer().analyze(source_path)

            self.assertFalse(marker_path.exists())

    def test_missing_file_raises_file_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            source_path = Path(temporary_root) / "missing.py"

            with self.assertRaises(FileNotFoundError):
                PythonASTAnalyzer().analyze(source_path)

    def test_directory_raises_is_a_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            directory_path = Path(temporary_root)

            with self.assertRaises(IsADirectoryError):
                PythonASTAnalyzer().analyze(directory_path)

    def test_invalid_python_raises_syntax_error(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            source_path = Path(temporary_root) / "invalid.py"

            source_path.write_text(
                "def broken(:\n"
                "    pass\n",
                encoding="utf-8",
            )

            with self.assertRaises(SyntaxError):
                PythonASTAnalyzer().analyze(source_path)


if __name__ == "__main__":
    unittest.main()