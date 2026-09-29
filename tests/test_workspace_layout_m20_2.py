"""M20.2 Workspace Layout tests."""

import unittest

from ui.visual_layout import (
    NavigationLayout,
    MainWorkspaceLayout,
    StatusLayout,
    WorkspaceLayout,
)


class M202WorkspaceLayoutTests(unittest.TestCase):

    def test_workspace_layout_is_immutable(self):
        layout = WorkspaceLayout()

        with self.assertRaises(AttributeError):
            layout.navigation = NavigationLayout()

    def test_workspace_layout_has_stable_top_level_regions(self):
        layout = WorkspaceLayout()

        self.assertEqual(
            layout.regions,
            ("navigation", "main_workspace", "status"),
        )

    def test_navigation_layout_has_stable_regions(self):
        layout = NavigationLayout()

        self.assertEqual(
            layout.regions,
            ("projects", "tasks", "history"),
        )

    def test_main_workspace_layout_has_stable_region(self):
        layout = MainWorkspaceLayout()

        self.assertEqual(
            layout.region,
            "main_workspace",
        )

    def test_status_layout_has_stable_regions(self):
        layout = StatusLayout()

        self.assertEqual(
            layout.regions,
            ("status", "execution", "activity"),
        )

    def test_app_accepts_workspace_layout(self):
        import tkinter as tk
        from ui.app import CodingAssistantApp

        root = tk.Tk()
        root.withdraw()
        try:
            layout = WorkspaceLayout()
            app = CodingAssistantApp(root, layout=layout)

            self.assertIs(app.layout, layout)
        finally:
            root.destroy()

    def test_app_defaults_to_workspace_layout(self):
        import tkinter as tk
        from ui.app import CodingAssistantApp

        root = tk.Tk()
        root.withdraw()
        try:
            app = CodingAssistantApp(root)

            self.assertIsInstance(app.layout, WorkspaceLayout)
        finally:
            root.destroy()

    def test_app_layout_preserves_top_level_contract(self):
        import tkinter as tk
        from ui.app import CodingAssistantApp

        root = tk.Tk()
        root.withdraw()
        try:
            app = CodingAssistantApp(root)

            self.assertEqual(
                app.layout.regions,
                ("navigation", "main_workspace", "status"),
            )
        finally:
            root.destroy()


if __name__ == "__main__":
    unittest.main()
