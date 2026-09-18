import tempfile
import unittest
from pathlib import Path

from agent_workflow.file_index import FileIndex, FileIndexEntry
from agent_workflow.project_scanner import ProjectScanner


class FileIndexTests(unittest.TestCase):
    def test_builds_index_from_scan_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)

            (project_path / "app.py").write_text(
                "print('ok')",
                encoding="utf-8",
            )
            (project_path / "README.md").write_text(
                "readme",
                encoding="utf-8",
            )
            (project_path / "data.csv").write_text(
                "a,b",
                encoding="utf-8",
            )

            scan_result = ProjectScanner(project_path).scan()
            index = FileIndex.from_scan_result(scan_result)

            self.assertEqual(index.root_path, project_path.resolve())
            self.assertEqual(
                index.entries,
                (
                    FileIndexEntry(
                        Path("app.py"),
                        ".py",
                        "python",
                    ),
                    FileIndexEntry(
                        Path("data.csv"),
                        ".csv",
                        "other",
                    ),
                    FileIndexEntry(
                        Path("README.md"),
                        ".md",
                        "markdown",
                    ),
                ),
            )

    def test_get_returns_matching_entry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            target = project_path / "app.py"
            target.write_text("print('ok')", encoding="utf-8")

            index = FileIndex.from_scan_result(
                ProjectScanner(project_path).scan()
            )

            result = index.get(Path("app.py"))

            self.assertEqual(
                result,
                FileIndexEntry(
                    Path("app.py"),
                    ".py",
                    "python",
                ),
            )

    def test_get_returns_none_for_missing_file(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            (project_path / "app.py").write_text(
                "print('ok')",
                encoding="utf-8",
            )

            index = FileIndex.from_scan_result(
                ProjectScanner(project_path).scan()
            )

            self.assertIsNone(index.get(Path("missing.py")))

    def test_index_is_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            (project_path / "app.py").write_text(
                "print('ok')",
                encoding="utf-8",
            )

            index = FileIndex.from_scan_result(
                ProjectScanner(project_path).scan()
            )

            with self.assertRaises(AttributeError):
                index.entries = ()

    def test_does_not_read_file_contents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            target = project_path / "app.py"
            original = "print('unchanged')\n"
            target.write_text(original, encoding="utf-8")

            FileIndex.from_scan_result(
                ProjectScanner(project_path).scan()
            )

            self.assertEqual(
                target.read_text(encoding="utf-8"),
                original,
            )


if __name__ == "__main__":
    unittest.main()