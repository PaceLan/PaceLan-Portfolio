import contextlib
import io
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import main
from history.history_core import HistoryStore


PROJECT_ROOT = Path(main.__file__).resolve().parent


class CliTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.history_temporary_directory = tempfile.TemporaryDirectory()
        self.history_store = HistoryStore(self.history_temporary_directory.name)

    def tearDown(self) -> None:
        self.history_temporary_directory.cleanup()

    def run_cli(self, inputs: list[str], history_store=None) -> str:
        output = io.StringIO()
        with patch("builtins.input", side_effect=inputs):
            with contextlib.redirect_stdout(output):
                main.main(history_store=history_store or self.history_store)
        return output.getvalue()


class ProjectTreeCliTests(CliTestCase):

    def test_show_project_tree_displays_directories_files_and_empty_directories(
        self,
    ) -> None:
        fixture_directory = Path(
            tempfile.mkdtemp(prefix="_cli_tree_", dir=PROJECT_ROOT)
        )
        try:
            nested_directory = fixture_directory / "nested"
            nested_directory.mkdir()
            (nested_directory / "example.py").write_text(
                "print('tree-test')\n",
                encoding="utf-8",
            )
            empty_directory = fixture_directory / "empty"
            empty_directory.mkdir()

            output = self.run_cli(["1", "5"])

            self.assertIn("Project Tree:", output)
            self.assertIn(f"[D] {fixture_directory.name}", output)
            self.assertIn("[D] nested", output)
            self.assertIn("[F] example.py", output)
            self.assertIn("[D] empty", output)
            self.assertIn("(empty)", output)
        finally:
            shutil.rmtree(fixture_directory, ignore_errors=True)


class CliInteractionTests(CliTestCase):
    def test_read_file_displays_contents(self) -> None:
        fixture_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                prefix="_cli_read_",
                dir=PROJECT_ROOT,
                delete=False,
                encoding="utf-8",
            ) as fixture:
                fixture.write("cli-read-marker")
                fixture_path = Path(fixture.name)

            output = self.run_cli(["2", fixture_path.name, "5"])

            self.assertIn("File Contents:", output)
            self.assertIn("cli-read-marker", output)
        finally:
            if fixture_path is not None:
                fixture_path.unlink(missing_ok=True)

    def test_write_file_creates_file_and_displays_result(self) -> None:
        fixture_directory = Path(
            tempfile.mkdtemp(prefix="_cli_write_", dir=PROJECT_ROOT)
        )
        target_path = fixture_directory / "created.txt"
        try:
            output = self.run_cli(
                ["3", str(target_path.relative_to(PROJECT_ROOT)), "cli-write-marker", "5"]
            )

            self.assertTrue(target_path.is_file())
            self.assertEqual(target_path.read_text(encoding="utf-8"), "cli-write-marker")
            self.assertIn("File written:", output)
        finally:
            shutil.rmtree(fixture_directory, ignore_errors=True)

    def test_invalid_menu_input_returns_to_menu(self) -> None:
        output = self.run_cli(["invalid", "5"])

        self.assertIn("Invalid option. Please select 1, 2, 3, 4, or 5.", output)
        self.assertIn("Exiting.", output)

    def test_eof_input_exits_cleanly(self) -> None:
        output = self.run_cli([EOFError()])

        self.assertIn("Exiting.", output)


class RunPythonFileCliTests(CliTestCase):
    def test_successful_python_execution(self) -> None:
        fixture_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                prefix="_cli_success_",
                dir=PROJECT_ROOT,
                delete=False,
                encoding="utf-8",
            ) as fixture:
                fixture.write("print('cli-success-marker')\n")
                fixture_path = Path(fixture.name)

            output = self.run_cli(["4", fixture_path.name, "5"])

            self.assertIn("Python stdout:", output)
            self.assertIn("cli-success-marker", output)
            self.assertIn("Python exit code: 0", output)
        finally:
            if fixture_path is not None:
                fixture_path.unlink(missing_ok=True)

    def test_missing_python_file(self) -> None:
        output = self.run_cli(["4", "_cli_missing_file.py", "5"])

        self.assertIn("Unable to run Python file", output)
        self.assertIn("File does not exist", output)

    def test_non_python_file(self) -> None:
        fixture_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                prefix="_cli_non_python_",
                dir=PROJECT_ROOT,
                delete=False,
                encoding="utf-8",
            ) as fixture:
                fixture.write("not Python")
                fixture_path = Path(fixture.name)

            output = self.run_cli(["4", fixture_path.name, "5"])

            self.assertIn("Unable to run Python file", output)
            self.assertIn("Path must refer to a .py file", output)
        finally:
            if fixture_path is not None:
                fixture_path.unlink(missing_ok=True)

    def test_directory_path(self) -> None:
        directory_path = Path(
            tempfile.mkdtemp(prefix="_cli_directory_", dir=PROJECT_ROOT)
        )
        try:
            output = self.run_cli(["4", directory_path.name, "5"])

            self.assertIn("Unable to run Python file", output)
            self.assertIn("Path is a directory", output)
        finally:
            shutil.rmtree(directory_path, ignore_errors=True)

    def test_outside_project_root_path(self) -> None:
        output = self.run_cli(["4", "..\\_cli_outside.py", "5"])

        self.assertIn("Unable to run Python file", output)
        self.assertIn("Path is outside the project root", output)


class HistoryCliIntegrationTests(CliTestCase):
    def test_successful_read_creates_one_history_entry_without_contents(self) -> None:
        fixture_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                prefix="_history_read_",
                dir=PROJECT_ROOT,
                delete=False,
                encoding="utf-8",
            ) as fixture:
                fixture.write("private-file-content")
                fixture_path = Path(fixture.name)

            self.run_cli(["2", fixture_path.name, "5"])

            entries = self.history_store.read_history()
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].operation, "read")
            self.assertTrue(entries[0].success)
            self.assertNotIn("private-file-content", self.history_store.history_path.read_text(encoding="utf-8"))
        finally:
            if fixture_path is not None:
                fixture_path.unlink(missing_ok=True)

    def test_failed_read_creates_one_failure_history_entry(self) -> None:
        self.run_cli(["2", "_history_missing.txt", "5"])

        entries = self.history_store.read_history()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].operation, "read")
        self.assertFalse(entries[0].success)
        self.assertEqual(entries[0].result, "FileNotFoundError")

    def test_successful_write_creates_one_history_entry(self) -> None:
        fixture_directory = Path(
            tempfile.mkdtemp(prefix="_history_write_", dir=PROJECT_ROOT)
        )
        try:
            target = fixture_directory / "created.txt"
            self.run_cli(
                ["3", str(target.relative_to(PROJECT_ROOT)), "safe-summary", "5"]
            )

            entries = self.history_store.read_history()
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].operation, "write")
            self.assertTrue(entries[0].success)
            self.assertEqual(target.read_text(encoding="utf-8"), "safe-summary")
        finally:
            shutil.rmtree(fixture_directory, ignore_errors=True)

    def test_failed_write_creates_one_failure_history_entry(self) -> None:
        fixture_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                prefix="_history_existing_",
                dir=PROJECT_ROOT,
                delete=False,
                encoding="utf-8",
            ) as fixture:
                fixture.write("existing")
                fixture_path = Path(fixture.name)

            self.run_cli(["3", fixture_path.name, "replacement", "5"])

            entries = self.history_store.read_history()
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].operation, "write")
            self.assertFalse(entries[0].success)
            self.assertEqual(entries[0].result, "FileExistsError")
            self.assertEqual(fixture_path.read_text(encoding="utf-8"), "existing")
        finally:
            if fixture_path is not None:
                fixture_path.unlink(missing_ok=True)

    def test_successful_run_creates_one_entry_without_stdout(self) -> None:
        fixture_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                prefix="_history_run_",
                dir=PROJECT_ROOT,
                delete=False,
                encoding="utf-8",
            ) as fixture:
                fixture.write("print('private-run-output')\n")
                fixture_path = Path(fixture.name)

            self.run_cli(["4", fixture_path.name, "5"])

            entries = self.history_store.read_history()
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].operation, "run")
            self.assertTrue(entries[0].success)
            self.assertNotIn("private-run-output", self.history_store.history_path.read_text(encoding="utf-8"))
        finally:
            if fixture_path is not None:
                fixture_path.unlink(missing_ok=True)

    def test_failed_run_creates_one_failure_entry_without_output(self) -> None:
        fixture_path = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".py",
                prefix="_history_failed_run_",
                dir=PROJECT_ROOT,
                delete=False,
                encoding="utf-8",
            ) as fixture:
                fixture.write(
                    "import sys\n"
                    "print('private-run-stdout')\n"
                    "print('private-run-stderr', file=sys.stderr)\n"
                    "sys.exit(2)\n"
                )
                fixture_path = Path(fixture.name)

            self.run_cli(["4", fixture_path.name, "5"])

            entries = self.history_store.read_history()
            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].operation, "run")
            self.assertFalse(entries[0].success)
            self.assertEqual(entries[0].result, "exit_code_2")
            persisted_text = self.history_store.history_path.read_text(encoding="utf-8")
            self.assertNotIn("private-run-stdout", persisted_text)
            self.assertNotIn("private-run-stderr", persisted_text)
        finally:
            if fixture_path is not None:
                fixture_path.unlink(missing_ok=True)

    def test_show_project_tree_creates_one_high_level_entry(self) -> None:
        self.run_cli(["1", "5"])

        entries = self.history_store.read_history()
        self.assertLessEqual(len(entries), 1)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].operation, "tree")
        self.assertEqual(entries[0].target, ".")
        self.assertTrue(entries[0].success)

    def test_history_failure_does_not_change_read_result(self) -> None:
        fixture_path = None

        class FailingHistoryStore:
            def append(self, entry) -> None:
                raise OSError("history storage unavailable")

        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                suffix=".txt",
                prefix="_history_failure_",
                dir=PROJECT_ROOT,
                delete=False,
                encoding="utf-8",
            ) as fixture:
                fixture.write("read-still-succeeds")
                fixture_path = Path(fixture.name)

            output = self.run_cli(["2", fixture_path.name, "5"], FailingHistoryStore())

            self.assertIn("File Contents:", output)
            self.assertIn("read-still-succeeds", output)
        finally:
            if fixture_path is not None:
                fixture_path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
