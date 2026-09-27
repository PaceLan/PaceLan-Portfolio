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

            info = manager.get_project_info()

            self.assertEqual(
                info["project_name"],
                project_path.name,
            )
            self.assertEqual(
                info["project_path"],
                project_path.resolve(),
            )
            self.assertTrue(info["exists"])
            self.assertTrue(info["is_directory"])

    def test_scan_project_returns_project_scan_result(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)

            (project_path / "src").mkdir()
            (project_path / "src" / "app.py").write_text(
                "print('ok')",
                encoding="utf-8",
            )

            manager = ProjectManager()
            manager.open_project(project_path)

            result = manager.scan_project()

            self.assertEqual(
                result.root_path,
                project_path.resolve(),
            )
            self.assertEqual(
                result.statistics.file_count,
                1,
            )
            self.assertEqual(
                result.files[0].relative_path,
                Path("src/app.py"),
            )
            self.assertTrue(result.successful)

    def test_scan_project_requires_open_project(self) -> None:
        manager = ProjectManager()

        with self.assertRaises(FileNotFoundError):
            manager.scan_project()


class FileReaderTests(unittest.TestCase):
    def test_read_file_returns_utf8_text(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            path = project_path / "example.txt"
            content = "Hello, 世界"

            path.write_text(content, encoding="utf-8")

            reader = FileReader(project_path)
            result = reader.read_file(path)

            self.assertEqual(result, content)

    def test_invalid_paths_raise_expected_exceptions(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            reader = FileReader(project_path)

            missing = project_path / "missing.txt"

            with self.assertRaises(FileNotFoundError):
                reader.read_file(missing)


class FileWriterTests(unittest.TestCase):
    def test_create_file_and_return_resolved_path(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            path = project_path / "created.txt"

            writer = FileWriter(project_path)
            result = writer.write_file(
                path,
                "hello",
            )

            self.assertEqual(result, path.resolve())
            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "hello",
            )

    def test_overwrite_requires_explicit_permission(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)
            path = project_path / "existing.txt"
            path.write_text("old", encoding="utf-8")

            writer = FileWriter(project_path)

            with self.assertRaises(FileExistsError):
                writer.write_file(path, "new")

            writer.write_file(
                path,
                "new",
                overwrite=True,
            )

            self.assertEqual(
                path.read_text(encoding="utf-8"),
                "new",
            )

    def test_rejects_outside_paths_directories_and_missing_parents(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            root = Path(temporary_root)
            writer = FileWriter(root)

            directory = root / "directory"
            directory.mkdir()

            with self.assertRaises(IsADirectoryError):
                writer.write_file(
                    directory,
                    "invalid",
                )

            missing_parent = root / "missing" / "file.txt"

            with self.assertRaises(FileNotFoundError):
                writer.write_file(
                    missing_parent,
                    "invalid",
                )


class ProjectTreeTests(unittest.TestCase):
    def test_build_tree_includes_nested_entries_and_ignores_unwanted_directories(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_path = Path(temporary_root)

            src = project_path / "src"
            nested = src / "nested"

            nested.mkdir(parents=True)

            (src / "app.py").write_text(
                "print('ok')",
                encoding="utf-8",
            )

            for ignored_name in (
                ".git",
                ".venv",
                "__pycache__",
            ):
                ignored = project_path / ignored_name
                ignored.mkdir()
                (ignored / "ignored.py").write_text(
                    "ignored",
                    encoding="utf-8",
                )

            tree = ProjectTree(project_path).build_tree()

            self.assertTrue(tree.is_directory)

            names = {
                child.name
                for child in tree.children
            }

            self.assertIn("src", names)
            self.assertNotIn(".git", names)
            self.assertNotIn(".venv", names)
            self.assertNotIn("__pycache__", names)

            src_node = next(
                child
                for child in tree.children
                if child.name == "src"
            )

            self.assertTrue(src_node.is_directory)

            src_names = {
                child.name
                for child in src_node.children
            }

            self.assertIn("app.py", src_names)
            self.assertIn("nested", src_names)


if __name__ == "__main__":
    unittest.main()