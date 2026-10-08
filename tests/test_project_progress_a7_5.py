import unittest

from application.development_tree import (
    DevelopmentNodeStatus,
    DevelopmentNodeType,
    DevelopmentTreeNode,
)
from application.project_progress import ProjectProgressView


class ProjectProgressViewTests(unittest.TestCase):
    def make_node(self, key, project_id, status, node_type=DevelopmentNodeType.MODULE):
        return DevelopmentTreeNode(
            node_id=key,
            project_id=project_id,
            node_key=key,
            node_type=node_type,
            status=status,
            title=key,
            completed_at=(
                "2026-10-08T10:00:00+00:00"
                if status is DevelopmentNodeStatus.COMPLETED
                else None
            ),
        )

    def test_project_progress_reports_overall_state(self):
        nodes = (
            self.make_node("C4", "project-1", DevelopmentNodeStatus.COMPLETED),
            self.make_node("C5", "project-1", DevelopmentNodeStatus.COMPLETED),
            self.make_node("C5.1", "project-1", DevelopmentNodeStatus.IN_PROGRESS),
            self.make_node("C6", "project-1", DevelopmentNodeStatus.PLANNED),
        )

        progress = ProjectProgressView(nodes).for_project("project-1")

        self.assertEqual(progress.total_modules, 4)
        self.assertEqual(progress.completed_modules, 2)
        self.assertEqual(progress.progress_percent, 50.0)
        self.assertEqual(progress.current_module, "C5.1")
        self.assertEqual(progress.remaining_modules, ("C5.1", "C6"))

    def test_project_isolation(self):
        nodes = (
            self.make_node("C5", "project-1", DevelopmentNodeStatus.COMPLETED),
            self.make_node("C6", "project-2", DevelopmentNodeStatus.PLANNED),
        )

        progress = ProjectProgressView(nodes).for_project("project-1")

        self.assertEqual(progress.total_modules, 1)
        self.assertEqual(progress.completed_modules, 1)
        self.assertEqual(progress.progress_percent, 100.0)
        self.assertIsNone(progress.current_module)
        self.assertEqual(progress.remaining_modules, ())

    def test_non_module_nodes_are_not_counted(self):
        nodes = (
            self.make_node("C5", "project-1", DevelopmentNodeStatus.COMPLETED),
            self.make_node(
                "run-1",
                "project-1",
                DevelopmentNodeStatus.IN_PROGRESS,
                DevelopmentNodeType.RUN,
            ),
        )

        progress = ProjectProgressView(nodes).for_project("project-1")

        self.assertEqual(progress.total_modules, 1)
        self.assertEqual(progress.completed_modules, 1)
        self.assertIsNone(progress.current_module)

    def test_unknown_project_has_zero_progress(self):
        progress = ProjectProgressView(()).for_project("project-1")

        self.assertEqual(progress.total_modules, 0)
        self.assertEqual(progress.completed_modules, 0)
        self.assertEqual(progress.progress_percent, 0.0)
        self.assertIsNone(progress.current_module)
        self.assertEqual(progress.remaining_modules, ())


if __name__ == "__main__":
    unittest.main()
