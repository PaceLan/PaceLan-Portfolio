import unittest


class VisualLayoutM194Tests(unittest.TestCase):
    def test_layout_module_exists(self):
        from ui.visual_layout import WorkspaceLayout

        self.assertIsNotNone(WorkspaceLayout)

    def test_workspace_layout_is_immutable(self):
        from ui.visual_layout import WorkspaceLayout

        layout = WorkspaceLayout()

        with self.assertRaises((AttributeError, TypeError)):
            layout.navigation = None

    def test_top_level_regions_are_stable(self):
        from ui.visual_layout import WorkspaceLayout

        layout = WorkspaceLayout()

        self.assertEqual(
            layout.regions,
            ("navigation", "main_workspace", "status"),
        )

    def test_navigation_regions_are_stable(self):
        from ui.visual_layout import WorkspaceLayout

        layout = WorkspaceLayout()

        self.assertEqual(
            layout.navigation.regions,
            ("projects", "tasks", "history"),
        )

    def test_status_regions_are_stable(self):
        from ui.visual_layout import WorkspaceLayout

        layout = WorkspaceLayout()

        self.assertEqual(
            layout.status.regions,
            ("status", "execution", "activity"),
        )

    def test_layout_subcomponents_are_immutable(self):
        from ui.visual_layout import WorkspaceLayout

        layout = WorkspaceLayout()

        with self.assertRaises((AttributeError, TypeError)):
            layout.navigation.regions = ("changed",)

        with self.assertRaises((AttributeError, TypeError)):
            layout.status.regions = ("changed",)


if __name__ == "__main__":
    unittest.main()
