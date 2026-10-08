import unittest

from application.development_tree import (
    DevelopmentNodeStatus,
    DevelopmentNodeType,
    DevelopmentTreeNode,
)
from application.development_tree_integration import (
    DevelopmentTreeIntegrationView,
)
from application.history import (
    AgentHistoryEntry,
    AgentHistoryStatus,
)


class DevelopmentTreeIntegrationTests(unittest.TestCase):
    def make_node(self, key, task_id=None, history_id=None):
        return DevelopmentTreeNode(
            node_id=key,
            project_id="project-1",
            node_key=key,
            node_type=DevelopmentNodeType.MODULE,
            status=DevelopmentNodeStatus.COMPLETED,
            title=key,
            task_id=task_id,
            history_id=history_id,
            completed_at="2026-10-08T11:00:00+00:00",
        )

    def make_history(self, history_id, task_id):
        return AgentHistoryEntry(
            history_id=history_id,
            project_id="project-1",
            task_id=task_id,
            execution_id="run-1",
            verification_status="passed",
            result_status=AgentHistoryStatus.COMPLETED,
            timestamp="2026-10-08T11:00:00+00:00",
        )

    def test_node_history_progress_and_verification_are_linked(self):
        node = self.make_node("C5.1", "task-1", "history-1")
        entry = self.make_history("history-1", "task-1")

        result = DevelopmentTreeIntegrationView((node,), (entry,)).for_node("C5.1")

        self.assertIs(result.node, node)
        self.assertIs(result.history, entry)
        self.assertEqual(result.progress_status, "completed")
        self.assertEqual(result.verification_status, "passed")

    def test_task_query_uses_tree_task_id(self):
        nodes = (
            self.make_node("C5.1", "task-1"),
            self.make_node("C5.2", "task-2"),
        )

        result = DevelopmentTreeIntegrationView(nodes).for_task("task-1")

        self.assertEqual(tuple(item.node.node_key for item in result), ("C5.1",))

    def test_missing_history_remains_unlinked(self):
        node = self.make_node("C5.1", "task-1", "missing-history")

        result = DevelopmentTreeIntegrationView((node,), ()).for_node("C5.1")

        self.assertIsNone(result.history)
        self.assertEqual(result.progress_status, "completed")
        self.assertIsNone(result.verification_status)

    def test_history_query(self):
        node = self.make_node("C5.1", "task-1", "history-1")
        result = DevelopmentTreeIntegrationView((node,)).for_history("history-1")

        self.assertEqual(tuple(item.node.node_key for item in result), ("C5.1",))


if __name__ == "__main__":
    unittest.main()
