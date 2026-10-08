import unittest

from application.development_history import (
    DevelopmentHistoryView,
)
from application.development_tree import (
    DevelopmentNodeStatus,
    DevelopmentNodeType,
    DevelopmentTreeNode,
)


class DevelopmentHistoryViewTests(unittest.TestCase):
    def make_node(self, key, started, summary):
        return DevelopmentTreeNode(
            node_id=key,
            project_id="project-1",
            node_key=key,
            node_type=DevelopmentNodeType.MODULE,
            status=DevelopmentNodeStatus.COMPLETED,
            title=key,
            started_at=started,
            completed_at=started,
            summary=summary,
        )

    def test_for_date_lists_modules_and_summaries(self):
        nodes = (
            self.make_node(
                "A7.1",
                "2026-10-07T10:00:00+00:00",
                "建立开发树模型",
            ),
            self.make_node(
                "A7.2",
                "2026-10-07T11:00:00+00:00",
                "建立开发树持久化",
            ),
        )
        day = DevelopmentHistoryView(nodes).for_date("2026-10-07")

        self.assertEqual(day.date, "2026-10-07")
        self.assertEqual(day.modules, ("A7.1", "A7.2"))
        self.assertEqual(
            day.summaries,
            ("建立开发树模型", "建立开发树持久化"),
        )

    def test_recent_returns_newest_days_first(self):
        nodes = (
            self.make_node(
                "A7.1",
                "2026-10-06T10:00:00+00:00",
                "历史",
            ),
            self.make_node(
                "A7.2",
                "2026-10-08T10:00:00+00:00",
                "持久化",
            ),
        )
        days = DevelopmentHistoryView(nodes).recent(2)

        self.assertEqual(
            tuple(day.date for day in days),
            ("2026-10-08", "2026-10-06"),
        )

    def test_non_module_nodes_are_not_reported_as_modules(self):
        node = DevelopmentTreeNode(
            node_id="run-1",
            project_id="project-1",
            node_key="run-1",
            node_type=DevelopmentNodeType.RUN,
            status=DevelopmentNodeStatus.COMPLETED,
            title="Run",
            completed_at="2026-10-08T10:00:00+00:00",
            summary="执行",
        )
        day = DevelopmentHistoryView((node,)).for_date("2026-10-08")

        self.assertEqual(day.modules, ())
        self.assertEqual(day.summaries, ())

    def test_invalid_date_is_rejected(self):
        with self.assertRaises(ValueError):
            DevelopmentHistoryView(()).for_date("not-a-date")


if __name__ == "__main__":
    unittest.main()
