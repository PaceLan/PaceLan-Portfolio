import json
import tempfile
import unittest
from pathlib import Path

from agent_workflow.project_context import (
    ProjectContext,
    ProjectContextBuilder,
)
from agent_workflow.project_scanner import ProjectScanner
from application.context_persistence import ContextPersistenceService
from application.context_storage import ContextStorage


class ContextPersistenceB4Tests(unittest.TestCase):
    def _build_context(self, root: Path) -> ProjectContext:
        (root / "main.py").write_text(
            "import helper\n\n"
            "class Main:\n"
            "    pass\n\n"
            "def run():\n"
            "    pass\n",
            encoding="utf-8",
        )
        (root / "helper.py").write_text(
            "def help_me():\n"
            "    pass\n",
            encoding="utf-8",
        )
        (root / "notes.md").write_text(
            "# Notes\n",
            encoding="utf-8",
        )

        scan = ProjectScanner(root).scan()
        return ProjectContextBuilder().build(scan)

    def test_round_trip_restores_complete_context(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = self._build_context(root)

            storage = ContextStorage()
            storage.save(context, root)

            restored = storage.load(root)

            self.assertIsInstance(restored, ProjectContext)
            self.assertEqual(restored.root_path, root.resolve())
            self.assertEqual(restored.scan_result.files, context.scan_result.files)
            self.assertEqual(
                restored.scan_result.directories,
                context.scan_result.directories,
            )
            self.assertEqual(
                restored.scan_result.statistics,
                context.scan_result.statistics,
            )
            self.assertEqual(
                restored.scan_result.errors,
                context.scan_result.errors,
            )
            self.assertEqual(restored.file_index, context.file_index)
            self.assertEqual(restored.python_asts, context.python_asts)
            self.assertEqual(
                restored.python_relationships,
                context.python_relationships,
            )
            self.assertEqual(
                restored.dependency_graph,
                context.dependency_graph,
            )

    def test_persistence_service_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = self._build_context(root)

            service = ContextPersistenceService()
            path = service.save(context, root)

            self.assertTrue(path.is_file())
            self.assertTrue(service.exists(root))
            self.assertEqual(service.load(root), context)

    def test_storage_is_project_local(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            context = self._build_context(root)

            path = ContextStorage().save(context, root)

            self.assertEqual(
                path,
                root / ".pacepilot" / "context.json",
            )

    def test_missing_storage_is_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):
                ContextStorage().load(Path(directory))

    def test_invalid_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            target = root / ".pacepilot" / "context.json"
            target.parent.mkdir()

            target.write_text(
                json.dumps(
                    {
                        "schema_version": 999,
                        "context": {},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                ContextStorage().load(root)


if __name__ == "__main__":
    unittest.main()
