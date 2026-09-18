import tempfile
import unittest
from pathlib import Path

from core.file_reader import FileReader
from core.file_writer import FileWriter
from core.project_manager import ProjectManager
from core.project_tree import ProjectTree


class ProjectManagerTests(unittest.TestCase):
    def test_open_project_and_get_project_information(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            manager = ProjectManager()

            manager.open_project(project_path)

            self.assertEqual(manager.get_project_path(), project_path.resolve())
            self.assertEqual(
                manager.get_project_info(),
                {
                    "project_name": project_path.name,
                    "project_path": project_path.resolve(),
                    "exists": True,
                    "is_directory": True,
                },
            )


class ProjectTreeTests(unittest.TestCase):
    def test_build_tree_includes_nested_entries_and_ignores_unwanted_directories(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            (project_path / "src" / "nested").mkdir(parents=True)
            (project_path / "src" / "app.py").write_text("print('ok')", encoding="utf-8")
            (project_path / "README.md").write_text("readme", encoding="utf-8")
            (project_path / ".git").mkdir()
            (project_path / "__pycache__").mkdir()
            (project_path / ".venv").mkdir()

            tree = ProjectTree(project_path).build_tree()

            self.assertTrue(tree.is_directory)
            self.assertEqual(tree.path, project_path.resolve())
            self.assertEqual(
                {child.name for child in tree.children},
                {"README.md", "src"},
            )
            src_node = next(child for child in tree.children if child.name == "src")
            self.assertTrue(src_node.is_directory)
            self.assertEqual({child.name for child in src_node.children}, {"app.py", "nested"})


class FileReaderTests(unittest.TestCase):
    def test_read_file_returns_utf8_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            expected_contents = "hello, world\nこんにちは"
            (project_path / "notes.txt").write_text(
                expected_contents,
                encoding="utf-8",
            )

            contents = FileReader(project_path).read_file("notes.txt")

            self.assertEqual(contents, expected_contents)
            self.assertIsInstance(contents, str)

    def test_invalid_paths_raise_expected_exceptions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            (project_path / "folder").mkdir()
            reader = FileReader(project_path)

            with self.assertRaises(FileNotFoundError):
                reader.read_file("missing.txt")
            with self.assertRaises(IsADirectoryError):
                reader.read_file("folder")
            with self.assertRaises(ValueError):
                reader.read_file("../outside.txt")


class FileWriterTests(unittest.TestCase):
    def test_create_file_and_return_resolved_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            writer = FileWriter(project_path)

            target = writer.write_file("notes.txt", "first")

            self.assertEqual(target, (project_path / "notes.txt").resolve())
            self.assertEqual(target.read_text(encoding="utf-8"), "first")

    def test_overwrite_requires_explicit_permission(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            target = project_path / "notes.txt"
            target.write_text("original", encoding="utf-8")
            writer = FileWriter(project_path)

            with self.assertRaises(FileExistsError):
                writer.write_file("notes.txt", "blocked")
            self.assertEqual(target.read_text(encoding="utf-8"), "original")

            writer.write_file("notes.txt", "updated", overwrite=True)
            self.assertEqual(target.read_text(encoding="utf-8"), "updated")

    def test_rejects_outside_paths_directories_and_missing_parents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            (project_path / "folder").mkdir()
            writer = FileWriter(project_path)

            with self.assertRaises(ValueError):
                writer.write_file("../outside.txt", "blocked")
            with self.assertRaises(IsADirectoryError):
                writer.write_file("folder", "blocked")
            with self.assertRaises(FileNotFoundError):
                writer.write_file("missing-parent/file.txt", "blocked")
            self.assertFalse((project_path / "missing-parent").exists())


if __name__ == "__main__":
    unittest.main()
