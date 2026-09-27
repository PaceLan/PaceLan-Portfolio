import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflow.project_scanner import (
    ProjectDirectory,
    ProjectScanResult,
    ProjectScanner,
)


class ProjectScannerTests(unittest.TestCase):
    def test_scan_discovers_files_recursively(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            (project_path / "src" / "nested").mkdir(parents=True)

            app = project_path / "src" / "app.py"
            readme = project_path / "README.md"

            app.write_text("print('ok')", encoding="utf-8")
            readme.write_text("readme", encoding="utf-8")

            result = ProjectScanner(project_path).scan()

            self.assertEqual(result.root_path, project_path.resolve())
            self.assertEqual(
                tuple(item.relative_path for item in result.files),
                (
                    Path("README.md"),
                    Path("src/app.py"),
                ),
            )

            readme_info = result.files[0]
            app_info = result.files[1]

            self.assertEqual(readme_info.extension, ".md")
            self.assertEqual(readme_info.name, "README.md")
            self.assertEqual(readme_info.size, readme.stat().st_size)
            self.assertEqual(readme_info.type, "file")

            self.assertEqual(app_info.extension, ".py")
            self.assertEqual(app_info.name, "app.py")
            self.assertEqual(app_info.size, app.stat().st_size)
            self.assertEqual(app_info.type, "file")

    def test_scan_ignores_existing_project_tree_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            (project_path / "src").mkdir()

            app = project_path / "src" / "app.py"
            app.write_text("print('ok')", encoding="utf-8")

            for ignored_name in (".git", ".venv", "__pycache__"):
                ignored_directory = project_path / ignored_name
                ignored_directory.mkdir()
                (ignored_directory / "ignored.py").write_text(
                    "ignored",
                    encoding="utf-8",
                )

            result = ProjectScanner(project_path).scan()

            self.assertEqual(
                tuple(item.relative_path for item in result.files),
                (Path("src/app.py"),),
            )
            self.assertEqual(result.statistics.file_count, 1)
            self.assertEqual(result.statistics.ignored_count, 3)

    def test_scan_returns_structured_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            (project_path / "src" / "nested").mkdir(parents=True)

            (project_path / "src" / "app.py").write_text(
                "print('ok')",
                encoding="utf-8",
            )

            result = ProjectScanner(project_path).scan()

            self.assertTrue(result.directories)
            self.assertTrue(
                all(
                    isinstance(directory, ProjectDirectory)
                    for directory in result.directories
                )
            )

            src = next(
                directory
                for directory in result.directories
                if directory.relative_path == Path("src")
            )

            self.assertIn(Path("src/app.py"), src.files)
            self.assertIn(
                Path("src/nested"),
                src.subdirectories,
            )

    def test_scan_returns_statistics(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)

            first = project_path / "a.txt"
            second = project_path / "b.py"

            first.write_text("abc", encoding="utf-8")
            second.write_text("12345", encoding="utf-8")

            result = ProjectScanner(project_path).scan()

            self.assertEqual(result.statistics.file_count, 2)
            self.assertEqual(result.statistics.directory_count, 1)
            self.assertEqual(
                result.statistics.total_size,
                first.stat().st_size + second.stat().st_size,
            )
            self.assertEqual(
                result.statistics.ignored_count,
                0,
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
            self.assertIsInstance(result.directories, tuple)
            self.assertIsInstance(result.errors, tuple)

            with self.assertRaises(AttributeError):
                result.files = ()

    def test_scan_successful_when_no_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            result = ProjectScanner(temporary_root).scan()

            self.assertTrue(result.successful)
            self.assertEqual(result.errors, ())

    def test_empty_project_returns_valid_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            result = ProjectScanner(temporary_root).scan()

            self.assertIsInstance(result, ProjectScanResult)
            self.assertEqual(result.files, ())
            self.assertEqual(
                result.statistics.file_count,
                0,
            )
            self.assertEqual(
                result.statistics.directory_count,
                1,
            )
            self.assertEqual(
                result.statistics.total_size,
                0,
            )
            self.assertEqual(result.errors, ())
            self.assertTrue(result.successful)

    def test_scan_does_not_read_or_modify_file_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            target = project_path / "app.py"

            original_contents = "print('unchanged')\n"

            target.write_text(
                original_contents,
                encoding="utf-8",
            )

            ProjectScanner(project_path).scan()

            self.assertEqual(
                target.read_text(encoding="utf-8"),
                original_contents,
            )

    def test_scan_records_directory_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)

            with patch.object(
                Path,
                "iterdir",
                side_effect=PermissionError("access denied"),
            ):
                result = ProjectScanner(project_path).scan()

            self.assertFalse(result.successful)
            self.assertTrue(result.errors)
            self.assertTrue(
                any(
                    "PermissionError" in error
                    for error in result.errors
                )
            )

    def test_missing_project_root_raises_file_not_found(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            missing_path = Path(temporary_root) / "missing"

            with self.assertRaises(FileNotFoundError):
                ProjectScanner(missing_path).scan()

    def test_file_project_root_raises_not_a_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_file = Path(temporary_root) / "project.txt"

            project_file.write_text(
                "not a directory",
                encoding="utf-8",
            )

            with self.assertRaises(NotADirectoryError):
                ProjectScanner(project_file).scan()

    def test_scan_uses_custom_ignore_rules(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)

            ignored = project_path / "build"
            ignored.mkdir()

            (ignored / "generated.py").write_text(
                "generated",
                encoding="utf-8",
            )

            source = project_path / "src.py"
            source.write_text(
                "print('ok')",
                encoding="utf-8",
            )

            result = ProjectScanner(
                project_path,
                ignored_directories={"build"},
            ).scan()

            self.assertEqual(
                tuple(item.relative_path for item in result.files),
                (Path("src.py"),),
            )
            self.assertEqual(
                result.statistics.ignored_count,
                1,
            )

    def test_scan_does_not_follow_directory_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)

            outside_path = (
                Path(temporary_root).parent
                / f"{Path(temporary_root).name}_outside"
            )

            outside_path.mkdir()

            try:
                (outside_path / "secret.py").write_text(
                    "outside",
                    encoding="utf-8",
                )

                link_path = project_path / "external"

                try:
                    link_path.symlink_to(
                        outside_path,
                        target_is_directory=True,
                    )
                except (OSError, NotImplementedError):
                    self.skipTest(
                        "Directory symlink creation is unavailable"
                    )

                result = ProjectScanner(project_path).scan()

                self.assertNotIn(
                    Path("external/secret.py"),
                    tuple(
                        item.relative_path
                        for item in result.files
                    ),
                )
            finally:
                if outside_path.exists():
                    for child in outside_path.iterdir():
                        child.unlink()
                    outside_path.rmdir()

    def test_scan_does_not_follow_file_symlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)

            outside_file = (
                Path(temporary_root).parent
                / f"{Path(temporary_root).name}_outside.py"
            )

            outside_file.write_text(
                "outside",
                encoding="utf-8",
            )

            try:
                link_path = project_path / "external.py"

                try:
                    link_path.symlink_to(outside_file)
                except (OSError, NotImplementedError):
                    self.skipTest(
                        "File symlink creation is unavailable"
                    )

                result = ProjectScanner(project_path).scan()

                self.assertNotIn(
                    Path("external.py"),
                    tuple(
                        item.relative_path
                        for item in result.files
                    ),
                )
            finally:
                if outside_file.exists():
                    outside_file.unlink()

    def test_scan_resolves_relative_project_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)

            (project_path / "app.py").write_text(
                "print('ok')",
                encoding="utf-8",
            )

            relative_root = Path(
                os.path.relpath(
                    project_path,
                    Path.cwd(),
                )
            )

            result = ProjectScanner(relative_root).scan()

            self.assertEqual(
                result.root_path,
                project_path.resolve(),
            )
            self.assertEqual(
                result.files[0].relative_path,
                Path("app.py"),
            )


if __name__ == "__main__":
    unittest.main()