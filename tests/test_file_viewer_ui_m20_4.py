import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import Mock

from application.workspace import ApplicationTreeNode
from ui.app import CodingAssistantApp


class M204FileViewerUiTests(unittest.TestCase):

    def _build_app(self, file_result=None):
        root = tk.Tk()
        root.withdraw()

        controller = Mock()
        project_root = Path(r"C:\project")
        controller.project_context.path = project_root
        controller.get_project_tree.return_value = ApplicationTreeNode(
            name="project",
            path=project_root,
            is_directory=True,
            children=(
                ApplicationTreeNode(
                    name="main.py",
                    path=project_root / "main.py",
                    is_directory=False,
                ),
            ),
        )

        if file_result is not None:
            controller.select_file.return_value = file_result

        app = CodingAssistantApp(root, controller=controller)
        app._load_project_tree()
        return root, app, controller

    def test_file_viewer_is_read_only(self):
        root, app, _ = self._build_app()
        try:
            self.assertEqual(str(app.file_viewer.cget("state")), "disabled")
        finally:
            root.destroy()

    def test_initial_viewer_has_no_selected_file(self):
        root, app, _ = self._build_app()
        try:
            self.assertEqual(
                app.file_path_label.cget("text"),
                "No file selected",
            )
            self.assertEqual(
                app.file_viewer.get("1.0", tk.END),
                "\n",
            )
        finally:
            root.destroy()

    def test_successful_file_selection_updates_path_and_contents(self):
        result = Mock(
            success=True,
            path="main.py",
            contents="print('hello')\n",
        )
        root, app, controller = self._build_app(result)
        try:
            project_item = app.tree_view.get_children("")[0]
            item = app.tree_view.get_children(project_item)[0]

            app.tree_view.selection_set(item)
            app._on_tree_selection(None)

            controller.select_file.assert_called_once_with("main.py")
            self.assertEqual(
                app.file_path_label.cget("text"),
                "main.py",
            )
            self.assertEqual(
                app.file_viewer.get("1.0", tk.END),
                "print('hello')\n\n",
            )
            self.assertEqual(
                str(app.file_viewer.cget("state")),
                "disabled",
            )
        finally:
            root.destroy()

    def test_failed_file_selection_clears_viewer(self):
        result = Mock(
            success=False,
            path="missing.py",
            contents="",
            error="missing",
        )
        root, app, controller = self._build_app(result)
        try:
            project_item = app.tree_view.get_children("")[0]
            item = app.tree_view.get_children(project_item)[0]

            app.tree_view.selection_set(item)
            app._on_tree_selection(None)

            controller.select_file.assert_called_once_with("main.py")
            self.assertEqual(
                app.file_path_label.cget("text"),
                "Unable to load file",
            )
            self.assertEqual(
                app.file_viewer.get("1.0", tk.END),
                "\n",
            )
            self.assertEqual(
                str(app.file_viewer.cget("state")),
                "disabled",
            )
        finally:
            root.destroy()

    def test_viewer_content_is_not_editable(self):
        root, app, _ = self._build_app()
        try:
            app._set_file_contents("original")
            self.assertEqual(
                str(app.file_viewer.cget("state")),
                "disabled",
            )
            self.assertEqual(
                app.file_viewer.get("1.0", tk.END),
                "original\n",
            )
        finally:
            root.destroy()

    def test_viewer_replaces_previous_content(self):
        root, app, _ = self._build_app()
        try:
            app._set_file_contents("first")
            app._set_file_contents("second")

            self.assertEqual(
                app.file_viewer.get("1.0", tk.END),
                "second\n",
            )
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
