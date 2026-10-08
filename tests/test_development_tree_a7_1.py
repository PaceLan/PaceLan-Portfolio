import unittest
from datetime import datetime, timezone

from application.development_tree import (
    DevelopmentNodeStatus,
    DevelopmentNodeType,
    DevelopmentTreeNode,
)


class DevelopmentTreeNodeTests(unittest.TestCase):
    def make_node(self, **overrides):
        values = {
            "node_id": "node-1",
            "project_id": "project-1",
            "node_key": "A7.1",
            "node_type": DevelopmentNodeType.MODULE,
            "status": DevelopmentNodeStatus.IN_PROGRESS,
            "title": "Development Tree Model",
        }
        values.update(overrides)
        return DevelopmentTreeNode(**values)

    def test_node_stores_tree_and_external_ids(self):
        node = self.make_node(
            parent_id="A7",
            task_id="task-1",
            run_id="run-1",
            history_id="history-1",
            summary="建立开发树节点模型",
        )
        self.assertEqual(node.project_id, "project-1")
        self.assertEqual(node.parent_id, "A7")
        self.assertEqual(node.task_id, "task-1")
        self.assertEqual(node.run_id, "run-1")
        self.assertEqual(node.history_id, "history-1")

    def test_completed_node_requires_completion_time(self):
        with self.assertRaises(ValueError):
            self.make_node(
                status=DevelopmentNodeStatus.COMPLETED,
            )

    def test_timestamp_is_validated(self):
        self.make_node(
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        with self.assertRaises(ValueError):
            self.make_node(started_at="not-a-timestamp")

    def test_node_is_immutable(self):
        node = self.make_node()
        with self.assertRaises(Exception):
            node.status = DevelopmentNodeStatus.COMPLETED

    def test_node_cannot_parent_itself(self):
        with self.assertRaises(ValueError):
            self.make_node(parent_id="node-1")


if __name__ == "__main__":
    unittest.main()
