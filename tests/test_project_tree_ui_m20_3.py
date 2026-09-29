import tkinter as tk
import unittest
from pathlib import Path
from unittest.mock import Mock

from application.workspace import ApplicationTreeNode
from ui.app import CodingAssistantApp


class M203ProjectTreeUiTests(unittest.TestCase):

    def _build_app(self):
        root = tk.Tk()
        root.withdraw()

        controller = Mock()
        project_root = Path(r"C:\project")
        controller.project_context.path = project_root

        tree = ApplicationTreeNode(
            name="project",
            path=project_root,
            is_directory=True,
            children=(
                ApplicationTreeNode(
                    name="src",
                    path=project_root / "src",
                    is_directory=True,
                    children=(
                        ApplicationTreeNode(
                            name="main.py",
                            path=project_root / "src" / "main.py",
                            is_directory=False,
                        ),
                    ),
                ),
                ApplicationTreeNode(
                    name="README.md",
                    path=project_root / "README.md",
                    is_directory=False,
                ),
            ),
        )
        controller.get_project_tree.return_value = tree

        app = CodingAssistantApp(root, controller=controller)
        return root, app

    def test_tree_node_names_are_mapped_to_treeview(self):
        root, app = self._build_app()
        try:
            app._load_project_tree()

            root_items = app.tree_view.get_children("")
            self.assertEqual(len(root_items), 1)
            self.assertEqual(
                app.tree_view.item(root_items[0], "text"),
                "project",
            )

            children = app.tree_view.get_children(root_items[0])
            self.assertEqual(
                [app.tree_view.item(item, "text") for item in children],
                ["src", "README.md"],
            )
        finally:
            root.destroy()

    def test_tree_hierarchy_is_preserved(self):
        root, app = self._build_app()
        try:
            app._load_project_tree()

            project_item = app.tree_view.get_children("")[0]
            src_item = app.tree_view.get_children(project_item)[0]
            src_children = app.tree_view.get_children(src_item)

            self.assertEqual(len(src_children), 1)
            self.assertEqual(
                app.tree_view.item(src_children[0], "text"),
                "main.py",
            )
        finally:
            root.destroy()

    def test_each_tree_item_has_stable_metadata(self):
        root, app = self._build_app()
        try:
            app._load_project_tree()

            items = []

            def collect(parent):
                for item in app.tree_view.get_children(parent):
                    items.append(item)
                    collect(item)

            collect("")

            self.assertEqual(len(items), 4)
            self.assertEqual(len(set(items)), 4)

            metadata = [app._tree_paths[item] for item in items]

            self.assertIn((".", True), metadata)
            self.assertIn(("src", True), metadata)
            self.assertIn(("src/main.py", False), metadata)
            self.assertIn(("README.md", False), metadata)
        finally:
            root.destroy()

    def test_directory_and_file_types_are_preserved(self):
        root, app = self._build_app()
        try:
            app._load_project_tree()

            self.assertTrue(
                any(is_directory for _, is_directory in app._tree_paths.values())
            )
            self.assertTrue(
                any(not is_directory for _, is_directory in app._tree_paths.values())
            )

            project_item = app.tree_view.get_children("")[0]
            src_item, readme_item = app.tree_view.get_children(project_item)

            self.assertTrue(app._tree_paths[src_item][1])
            self.assertFalse(app._tree_paths[readme_item][1])
        finally:
            root.destroy()

    def test_tree_rendering_does_not_replace_application_tree_model(self):
        root, app = self._build_app()
        try:
            model = app.controller.get_project_tree()
            app._load_project_tree()

            self.assertIs(model, app.controller.get_project_tree.return_value)
            self.assertEqual(model.name, "project")
            self.assertEqual(model.children[0].name, "src")
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
