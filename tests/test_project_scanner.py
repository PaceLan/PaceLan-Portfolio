import tempfile
import unittest
from pathlib import Path

from agent_workflow.project_scanner import (
    ProjectFile,
    ProjectScanResult,
    ProjectScanner,
)


class ProjectScannerTests(unittest.TestCase):
    def test_scan_discovers_files_recursively(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            (project_path / "src" / "nested").mkdir(parents=True)
            (project_path / "src" / "app.py").write_text(
                "print('ok')",
                encoding="utf-8",
            )
            (project_path / "README.md").write_text(
                "readme",
                encoding="utf-8",
            )

            result = ProjectScanner(project_path).scan()

            self.assertEqual(result.root_path, project_path.resolve())
            self.assertEqual(
                result.files,
                (
                    ProjectFile(
                        relative_path=Path("README.md"),
                        extension=".md",
                    ),
                    ProjectFile(
                        relative_path=Path("src/app.py"),
                        extension=".py",
                    ),
                ),
            )

    def test_scan_ignores_existing_project_tree_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            (project_path / "src").mkdir()
            (project_path / "src" / "app.py").write_text(
                "print('ok')",
                encoding="utf-8",
            )

            for ignored_name in (".git", ".venv", "__pycache__"):
                ignored_directory = project_path / ignored_name
                ignored_directory.mkdir()
                (ignored_directory / "ignored.py").write_text(
                    "ignored",
                    encoding="utf-8",
                )

            result = ProjectScanner(project_path).scan()

            self.assertEqual(
                result.files,
                (
                    ProjectFile(
                        relative_path=Path("src/app.py"),
                        extension=".py",
                    ),
                ),
            )

    def test_scan_returns_immutable_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            (project_path / "app.py").write_text(
                "print('ok')",
                encoding="utf-8",
            )

            result = ProjectScanner(project_path).scan()

            self.assertIsInstance(result, ProjectScanResult)
            self.assertIsInstance(result.files, tuple)

            with self.assertRaises(AttributeError):
                result.files = ()

    def test_scan_does_not_read_or_modify_file_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            target = project_path / "app.py"
            original_contents = "print('unchanged')\n"
            target.write_text(original_contents, encoding="utf-8")

            ProjectScanner(project_path).scan()

            self.assertEqual(
                target.read_text(encoding="utf-8"),
                original_contents,
            )

    def test_missing_project_root_raises_file_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            missing_path = Path(temporary_root) / "missing"

            with self.assertRaises(FileNotFoundError):
                ProjectScanner(missing_path).scan()

    def test_file_project_root_raises_not_a_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_file = Path(temporary_root) / "project.txt"
            project_file.write_text("not a directory", encoding="utf-8")

            with self.assertRaises(NotADirectoryError):
                ProjectScanner(project_file).scan()


if __name__ == "__main__":
    unittest.main()