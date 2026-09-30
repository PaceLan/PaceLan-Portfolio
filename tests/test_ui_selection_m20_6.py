import unittest
from pathlib import Path
from unittest.mock import Mock

from application.workspace import ApplicationTreeNode
from ui.app import CodingAssistantApp
from ui.controller import ApplicationController, FileLoadResult, ProjectContext
from ui.workspace_state import (
    SelectedFile,
    TreeState,
    ViewerState,
    WorkspaceState,
)


class M206SelectionStateTests(unittest.TestCase):

    def _app_without_tk(self):
        app = CodingAssistantApp.__new__(CodingAssistantApp)
        app.controller = Mock(spec=ApplicationController)
        app.workspace_state = WorkspaceState(
            project=ProjectContext(
                "project",
                Path(r"C:\project"),
                True,
                True,
            ),
            tree=TreeState(loaded=True),
            selected_file=SelectedFile(),
            viewer=ViewerState(),
            status="Project loaded",
        )
        app._tree_paths = {"file": ("src/main.py", False)}
        app._clear_file_viewer = Mock()
        app._set_file_contents = Mock()
        app.file_path_label = Mock()
        app.status_label = Mock()
        app.tree_view = Mock()
        return app

    def test_file_selection_updates_tree_selection(self):
        app = self._app_without_tk()
        app.tree_view.selection.return_value = ("file",)
        app.controller.select_file.return_value = FileLoadResult(
            "src/main.py",
            True,
            contents="print('ok')",
        )

        app._on_tree_selection(None)

        self.assertEqual(
            app.workspace_state.tree.selected_path,
            "src/main.py",
        )
        self.assertFalse(
            app.workspace_state.tree.selected_is_directory
        )

    def test_file_selection_updates_selected_file(self):
        app = self._app_without_tk()
        app.tree_view.selection.return_value = ("file",)
        app.controller.select_file.return_value = FileLoadResult(
            "src/main.py",
            True,
            contents="print('ok')",
        )

        app._on_tree_selection(None)

        self.assertEqual(
            app.workspace_state.selected_file.path,
            "src/main.py",
        )

    def test_file_selection_updates_viewer_state(self):
        app = self._app_without_tk()
        app.tree_view.selection.return_value = ("file",)
        app.controller.select_file.return_value = FileLoadResult(
            "src/main.py",
            True,
            contents="print('ok')",
        )

        app._on_tree_selection(None)

        self.assertTrue(app.workspace_state.viewer.loaded)
        self.assertEqual(
            app.workspace_state.viewer.path,
            "src/main.py",
        )
        self.assertEqual(
            app.workspace_state.viewer.contents,
            "print('ok')",
        )

    def test_file_selection_updates_status(self):
        app = self._app_without_tk()
        app.tree_view.selection.return_value = ("file",)
        app.controller.select_file.return_value = FileLoadResult(
            "src/main.py",
            True,
            contents="print('ok')",
        )

        app._on_tree_selection(None)

        self.assertEqual(
            app.workspace_state.status,
            "Loaded: src/main.py",
        )

    def test_failed_selection_keeps_selected_path(self):
        app = self._app_without_tk()
        app.tree_view.selection.return_value = ("file",)
        app.controller.select_file.return_value = FileLoadResult(
            "src/main.py",
            False,
            error="not found",
        )

        app._on_tree_selection(None)

        self.assertEqual(
            app.workspace_state.tree.selected_path,
            "src/main.py",
        )
        self.assertEqual(
            app.workspace_state.selected_file.path,
            "src/main.py",
        )

    def test_failed_selection_creates_failed_viewer_state(self):
        app = self._app_without_tk()
        app.tree_view.selection.return_value = ("file",)
        app.controller.select_file.return_value = FileLoadResult(
            "src/main.py",
            False,
            error="not found",
        )

        app._on_tree_selection(None)

        self.assertFalse(app.workspace_state.viewer.loaded)
        self.assertEqual(
            app.workspace_state.viewer.path,
            "src/main.py",
        )
        self.assertEqual(
            app.workspace_state.viewer.error,
            "not found",
        )

    def test_empty_selection_does_not_change_state(self):
        app = self._app_without_tk()
        before = app.workspace_state
        app.tree_view.selection.return_value = ()

        app._on_tree_selection(None)

        self.assertEqual(app.workspace_state, before)
        app.controller.select_file.assert_not_called()

    def test_directory_selection_clears_file_state(self):
        app = self._app_without_tk()
        app.tree_view.selection.return_value = ("directory",)
        app._tree_paths["directory"] = ("src", True)

        app._on_tree_selection(None)

        self.assertEqual(
            app.workspace_state.tree.selected_path,
            "src",
        )
        self.assertTrue(
            app.workspace_state.tree.selected_is_directory
        )
        self.assertIsNone(
            app.workspace_state.selected_file.path
        )
        self.assertFalse(
            app.workspace_state.viewer.loaded
        )
        app.controller.select_file.assert_not_called()

    def test_selection_uses_controller_boundary(self):
        app = self._app_without_tk()
        app.tree_view.selection.return_value = ("file",)
        app.controller.select_file.return_value = FileLoadResult(
            "src/main.py",
            True,
            contents="print('ok')",
        )

        app._on_tree_selection(None)

        app.controller.select_file.assert_called_once_with(
            "src/main.py"
        )


if __name__ == "__main__":
    unittest.main()
