import unittest

from application.development_tree import (
    DevelopmentNodeStatus,
    DevelopmentNodeType,
    DevelopmentTreeNode,
)
from application.module_progress import ModuleProgressView


class ModuleProgressViewTests(unittest.TestCase):
    def make_node(self, key, status):
        return DevelopmentTreeNode(
            node_id=key,
            project_id="project-1",
            node_key=key,
            node_type=DevelopmentNodeType.MODULE,
            status=status,
            title=key,
            completed_at=(
                "2026-10-08T10:00:00+00:00"
                if status is DevelopmentNodeStatus.COMPLETED
                else None
            ),
        )

    def test_module_progress_reports_completed_current_and_remaining(self):
        nodes = (
            self.make_node("C5", DevelopmentNodeStatus.COMPLETED),
            self.make_node("C5.1", DevelopmentNodeStatus.COMPLETED),
            self.make_node("C5.2", DevelopmentNodeStatus.IN_PROGRESS),
            self.make_node("C5.3", DevelopmentNodeStatus.PLANNED),
        )

        progress = ModuleProgressView(nodes).for_module("C5")

        self.assertEqual(progress.total_nodes, 4)
        self.assertEqual(progress.completed_nodes, 2)
        self.assertEqual(progress.progress_percent, 50.0)
        self.assertEqual(progress.current_node, "C5.2")
        self.assertEqual(progress.remaining_nodes, ("C5.2", "C5.3"))

    def test_module_isolation(self):
        nodes = (
            self.make_node("C5.1", DevelopmentNodeStatus.COMPLETED),
            self.make_node("C6.1", DevelopmentNodeStatus.PLANNED),
        )

        progress = ModuleProgressView(nodes).for_module("C5")

        self.assertEqual(progress.total_nodes, 1)
        self.assertEqual(progress.completed_nodes, 1)
        self.assertEqual(progress.progress_percent, 100.0)
        self.assertIsNone(progress.current_node)
        self.assertEqual(progress.remaining_nodes, ())

    def test_unknown_module_has_zero_progress(self):
        progress = ModuleProgressView(()).for_module("C5.5")

        self.assertEqual(progress.total_nodes, 0)
        self.assertEqual(progress.completed_nodes, 0)
        self.assertEqual(progress.progress_percent, 0.0)
        self.assertIsNone(progress.current_node)
        self.assertEqual(progress.remaining_nodes, ())


if __name__ == "__main__":
    unittest.main()
