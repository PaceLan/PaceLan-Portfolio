import json
import tempfile
import unittest
from pathlib import Path

from application.workspace import ProjectWorkspaceService
from history.history_core import HistoryStore
from ui.controller import ApplicationController


class ProjectLifecycleM235Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project = Path(self.temp_dir.name) / "project"
        self.project.mkdir()
        (self.project / "main.py").write_text(
            "print('hello')\n",
            encoding="utf-8",
        )
        self.workspace = ProjectWorkspaceService()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_open_project_and_read_file(self):
        info = self.workspace.open_project(self.project)

        self.assertEqual(info["project_path"], self.project.resolve())
        self.assertEqual(
            self.workspace.read_file("main.py"),
            "print('hello')\n",
        )

    def test_close_project_clears_workspace(self):
        self.workspace.open_project(self.project)

        self.workspace.close_project()

        self.assertIsNone(self.workspace.project_path)
        with self.assertRaises(ValueError):
            self.workspace.read_file("main.py")

    def test_persist_creates_recoverable_snapshot_and_history(self):
        self.workspace.open_project(self.project)

        snapshot = self.workspace.persist_project()

        self.assertTrue(snapshot.snapshot_id)
        self.assertEqual(snapshot.file_count, 1)

        history = HistoryStore(self.project / "history").read_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].operation, "persist_project")
        self.assertEqual(history[0].result, snapshot.snapshot_id)
        self.assertTrue(history[0].success)

    def test_reopen_restores_workspace_access(self):
        self.workspace.open_project(self.project)
        self.workspace.close_project()

        with self.assertRaises(ValueError):
            self.workspace.reopen_project()

    def test_controller_lifecycle(self):
        controller = ApplicationController()

        context = controller.open_project(self.project)
        self.assertEqual(context.path, self.project.resolve())

        snapshot = controller.persist_project()
        self.assertTrue(snapshot.snapshot_id)

        controller.close_project()
        self.assertIsNone(controller.initial_state().project.path)

        context = controller.open_project(self.project)
        self.assertEqual(context.path, self.project.resolve())


if __name__ == "__main__":
    unittest.main()
