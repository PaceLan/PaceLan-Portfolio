import unittest
from pathlib import Path

from ui.controller import ApplicationController, ProjectContext
from ui.workspace_state import (
    SelectedFile,
    TreeState,
    ViewerState,
    WorkspaceState,
)


class M205WorkspaceStateTests(unittest.TestCase):

    def test_state_models_are_immutable(self):
        state = WorkspaceState(project=ProjectContext(None, None, False, False))

        with self.assertRaises(Exception):
            state.status = "Changed"

        with self.assertRaises(Exception):
            state.tree = TreeState(loaded=True)

    def test_controller_initial_state_returns_workspace_state(self):
        controller = ApplicationController()
        state = controller.initial_state()

        self.assertIsInstance(state, WorkspaceState)
        self.assertIsInstance(state.project, ProjectContext)
        self.assertEqual(state.status, "Ready")
        self.assertFalse(state.tree.loaded)
        self.assertIsNone(state.selected_file.path)
        self.assertFalse(state.viewer.loaded)

    def test_initial_state_is_empty_and_ready(self):
        controller = ApplicationController()
        state = controller.initial_state()

        self.assertEqual(state.project.path, None)
        self.assertFalse(state.tree.loaded)
        self.assertIsNone(state.tree.selected_path)
        self.assertFalse(state.tree.selected_is_directory)
        self.assertIsNone(state.selected_file.path)
        self.assertEqual(state.viewer.contents, "")
        self.assertIsNone(state.viewer.error)
        self.assertEqual(state.status, "Ready")

    def test_selected_file_is_independent_state(self):
        selected = SelectedFile(path="src/main.py")
        viewer = ViewerState(
            path="src/main.py",
            contents="print('ok')",
            loaded=True,
        )

        self.assertEqual(selected.path, viewer.path)
        self.assertTrue(viewer.loaded)

    def test_tree_state_tracks_selection(self):
        tree = TreeState(
            loaded=True,
            selected_path="src/main.py",
            selected_is_directory=False,
        )

        self.assertTrue(tree.loaded)
        self.assertEqual(tree.selected_path, "src/main.py")
        self.assertFalse(tree.selected_is_directory)

    def test_directory_selection_has_no_selected_file(self):
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

        self.assertTrue(state.tree.selected_is_directory)
        self.assertEqual(state.tree.selected_path, "src")
        self.assertIsNone(state.selected_file.path)
        self.assertFalse(state.viewer.loaded)

    def test_loaded_file_state_forms_complete_chain(self):
        project = ProjectContext(
            "project",
            Path(r"C:\project"),
            True,
            True,
        )

        state = WorkspaceState(
            project=project,
            tree=TreeState(
                loaded=True,
                selected_path="src/main.py",
            ),
            selected_file=SelectedFile(path="src/main.py"),
            viewer=ViewerState(
                path="src/main.py",
                contents="print('ok')",
                loaded=True,
            ),
            status="Loaded: src/main.py",
        )

        self.assertEqual(
            state.project.path,
            Path(r"C:\project"),
        )
        self.assertEqual(
            state.tree.selected_path,
            state.selected_file.path,
        )
        self.assertEqual(
            state.selected_file.path,
            state.viewer.path,
        )
        self.assertTrue(state.viewer.loaded)
        self.assertEqual(state.status, "Loaded: src/main.py")

    def test_failed_viewer_state_preserves_selected_path(self):
        state = WorkspaceState(
            project=ProjectContext(None, None, False, False),
            tree=TreeState(
                loaded=True,
                selected_path="missing.py",
            ),
            selected_file=SelectedFile(path="missing.py"),
            viewer=ViewerState(
                path="missing.py",
                loaded=False,
                error="not found",
            ),
            status="Unable to load file",
        )

        self.assertEqual(
            state.tree.selected_path,
            state.selected_file.path,
        )
        self.assertEqual(
            state.selected_file.path,
            state.viewer.path,
        )
        self.assertFalse(state.viewer.loaded)
        self.assertEqual(state.viewer.error, "not found")
        self.assertEqual(state.status, "Unable to load file")


if __name__ == "__main__":
    unittest.main()
