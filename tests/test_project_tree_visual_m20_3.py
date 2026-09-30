import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import Mock

from application.workspace import ApplicationTreeNode
from ui.app import CodingAssistantApp


class M203VisualTreeTests(unittest.TestCase):

    def test_tree_items_expose_directory_file_visual_state(self):
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
                    name="src",
                    path=project_root / "src",
                    is_directory=True,
                ),
                ApplicationTreeNode(
                    name="main.py",
                    path=project_root / "main.py",
                    is_directory=False,
                ),
            ),
        )

        app = CodingAssistantApp(root, controller=controller)
        try:
            app._load_project_tree()

            project_item = app.tree_view.get_children("")[0]
            src_item, file_item = app.tree_view.get_children(project_item)

            self.assertTrue(app._tree_paths[src_item][1])
            self.assertFalse(app._tree_paths[file_item][1])

            self.assertEqual(
                app.tree_view.item(src_item, "text"),
                "src",
            )
            self.assertEqual(
                app.tree_view.item(file_item, "text"),
                "main.py",
            )
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
