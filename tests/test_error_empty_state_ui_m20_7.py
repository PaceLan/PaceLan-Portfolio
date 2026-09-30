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


class M207ErrorEmptyStateTests(unittest.TestCase):

    def _app(self):
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
        app._tree_paths = {}
        app._clear_file_viewer = Mock()
        app._set_file_contents = Mock()
        app.file_path_label = Mock()
        app.status_label = Mock()
        app.tree_view = Mock()
        return app

    def test_initial_state_is_empty_and_ready(self):
        controller = ApplicationController()

        state = controller.initial_state()

        self.assertEqual(state.status, "Ready")
        self.assertFalse(state.tree.loaded)
        self.assertIsNone(state.tree.selected_path)
        self.assertFalse(state.tree.selected_is_directory)
        self.assertIsNone(state.selected_file.path)
        self.assertIsNone(state.viewer.path)
        self.assertEqual(state.viewer.contents, "")
        self.assertFalse(state.viewer.loaded)
        self.assertIsNone(state.viewer.error)

    def test_empty_tree_selection_preserves_state(self):
        app = self._app()
        before = app.workspace_state
        app.tree_view.selection.return_value = ()

        app._on_tree_selection(None)

        self.assertEqual(app.workspace_state, before)
        app.controller.select_file.assert_not_called()

    def test_directory_selection_produces_empty_viewer_state(self):
        app = self._app()
        app._tree_paths["directory"] = ("src", True)
        app.tree_view.selection.return_value = ("directory",)

        app._on_tree_selection(None)

        self.assertEqual(app.workspace_state.tree.selected_path, "src")
        self.assertTrue(app.workspace_state.tree.selected_is_directory)
        self.assertIsNone(app.workspace_state.selected_file.path)
        self.assertIsNone(app.workspace_state.viewer.path)
        self.assertEqual(app.workspace_state.viewer.contents, "")
        self.assertFalse(app.workspace_state.viewer.loaded)
        self.assertIsNone(app.workspace_state.viewer.error)
        self.assertEqual(
            app.workspace_state.status,
            "Selected directory: src",
        )
        app.controller.select_file.assert_not_called()

    def test_failed_file_selection_produces_error_state(self):
        app = self._app()
        app._tree_paths["file"] = ("missing.py", False)
        app.tree_view.selection.return_value = ("file",)
        app.controller.select_file.return_value = FileLoadResult(
            "missing.py",
            False,
            error="File does not exist",
        )

        app._on_tree_selection(None)

        self.assertEqual(
            app.workspace_state.tree.selected_path,
            "missing.py",
        )
        self.assertFalse(
            app.workspace_state.tree.selected_is_directory,
        )
        self.assertEqual(
            app.workspace_state.selected_file.path,
            "missing.py",
        )
        self.assertEqual(
            app.workspace_state.viewer.path,
            "missing.py",
        )
        self.assertEqual(
            app.workspace_state.viewer.contents,
            "",
        )
        self.assertFalse(
            app.workspace_state.viewer.loaded,
        )
        self.assertEqual(
            app.workspace_state.viewer.error,
            "File does not exist",
        )
        self.assertEqual(
            app.workspace_state.status,
            "Unable to load file",
        )

    def test_failed_file_selection_clears_visible_file_content(self):
        app = self._app()
        app._tree_paths["file"] = ("missing.py", False)
        app.tree_view.selection.return_value = ("file",)
        app.controller.select_file.return_value = FileLoadResult(
            "missing.py",
            False,
            error="File does not exist",
        )

        app._on_tree_selection(None)

        app._clear_file_viewer.assert_called_once_with(
            "Unable to load file",
        )
        app.status_label.configure.assert_called_once_with(
            text="Unable to load file",
        )

    def test_empty_viewer_can_be_represented_without_error(self):
        state = WorkspaceState(
            project=ProjectContext(
                "project",
                Path(r"C:\project"),
                True,
                True,
            ),
            tree=TreeState(
                loaded=True,
                selected_path="src",
                selected_is_directory=True,
            ),
            selected_file=SelectedFile(),
            viewer=ViewerState(),
            status="Selected directory: src",
        )

        self.assertEqual(state.viewer.contents, "")
        self.assertFalse(state.viewer.loaded)
        self.assertIsNone(state.viewer.error)

    def test_error_state_preserves_error_message(self):
        state = WorkspaceState(
            project=ProjectContext(
                "project",
                Path(r"C:\project"),
                True,
                True,
            ),
            tree=TreeState(
                loaded=True,
                selected_path="missing.py",
            ),
            selected_file=SelectedFile(path="missing.py"),
            viewer=ViewerState(
                path="missing.py",
                contents="",
                loaded=False,
                error="Permission denied",
            ),
            status="Unable to load file",
        )

        self.assertFalse(state.viewer.loaded)
        self.assertEqual(state.viewer.error, "Permission denied")
        self.assertEqual(state.viewer.contents, "")
        self.assertEqual(state.status, "Unable to load file")


if __name__ == "__main__":
    unittest.main()
