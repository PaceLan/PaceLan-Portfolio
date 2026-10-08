import unittest

from application.development_tree import (
    DevelopmentNodeStatus,
    DevelopmentNodeType,
    DevelopmentTreeNode,
)
from application.development_tree_query import DevelopmentTreeQuery


class DevelopmentTreeQueryTests(unittest.TestCase):
    def make_node(self, key, project, status, started="2026-10-08T10:00:00+00:00"):
        return DevelopmentTreeNode(
            node_id=key,
            project_id=project,
            node_key=key,
            node_type=DevelopmentNodeType.MODULE,
            status=status,
            title=key,
            started_at=started,
            completed_at=(
                "2026-10-08T11:00:00+00:00"
                if status is DevelopmentNodeStatus.COMPLETED
                else None
            ),
        )

    def setUp(self):
        self.nodes = (
            self.make_node("C5", "p1", DevelopmentNodeStatus.COMPLETED),
            self.make_node("C5.1", "p1", DevelopmentNodeStatus.IN_PROGRESS),
            self.make_node("C5.2", "p1", DevelopmentNodeStatus.BLOCKED),
            self.make_node("C6", "p2", DevelopmentNodeStatus.PLANNED),
        )
        self.query = DevelopmentTreeQuery(self.nodes)

    def test_query_by_date(self):
        self.assertEqual(
            tuple(node.node_key for node in self.query.by_date("2026-10-08")),
            ("C5", "C5.1", "C5.2", "C6"),
        )

    def test_query_by_module(self):
        self.assertEqual(
            tuple(node.node_key for node in self.query.by_module("C5")),
            ("C5", "C5.1", "C5.2"),
        )

    def test_query_by_project(self):
        self.assertEqual(
            tuple(node.node_key for node in self.query.by_project("p1")),
            ("C5", "C5.1", "C5.2"),
        )

    def test_status_queries(self):
        self.assertEqual(
            tuple(node.node_key for node in self.query.in_progress()),
            ("C5.1",),
        )
        self.assertEqual(
            tuple(node.node_key for node in self.query.completed()),
            ("C5",),
        )
        self.assertEqual(
            tuple(node.node_key for node in self.query.blocked()),
            ("C5.2",),
        )

    def test_remaining_excludes_completed_and_cancelled(self):
        cancelled = self.make_node("C7", "p1", DevelopmentNodeStatus.CANCELLED)
        query = DevelopmentTreeQuery(self.nodes + (cancelled,))

        self.assertEqual(
            tuple(node.node_key for node in query.remaining()),
            ("C5.1", "C5.2", "C6"),
        )

    def test_invalid_date_is_rejected(self):
        with self.assertRaises(ValueError):
            self.query.by_date("not-a-date")


if __name__ == "__main__":
    unittest.main()
