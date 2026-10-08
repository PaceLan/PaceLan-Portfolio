import tempfile
import unittest
from pathlib import Path

from application.development_tree import (
    DevelopmentNodeStatus,
    DevelopmentNodeType,
    DevelopmentTreeNode,
)
from application.development_tree_storage import DevelopmentTreeStorage


class DevelopmentTreeStorageTests(unittest.TestCase):
    def make_tree(self):
        return (
            DevelopmentTreeNode(
                node_id="root",
                project_id="project-1",
                node_key="A7",
                node_type=DevelopmentNodeType.MODULE,
                status=DevelopmentNodeStatus.COMPLETED,
                title="Development Tree",
                completed_at="2026-10-08T00:00:00+00:00",
            ),
            DevelopmentTreeNode(
                node_id="child",
                project_id="project-1",
                node_key="A7.2",
                node_type=DevelopmentNodeType.MODULE,
                status=DevelopmentNodeStatus.IN_PROGRESS,
                title="Development Tree Persistence",
                parent_id="root",
                task_id="task-7",
                run_id="run-7",
                history_id="history-7",
                summary="Persist the complete development tree.",
            ),
        )

    def test_round_trip_survives_reload(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = DevelopmentTreeStorage()
            tree = self.make_tree()

            storage.save(directory, tree)
            restored = storage.load(directory)

            self.assertEqual(restored, tree)

    def test_missing_storage_returns_empty_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                DevelopmentTreeStorage().load(directory),
                (),
            )

    def test_storage_is_independent_file(self):
        with tempfile.TemporaryDirectory() as directory:
            DevelopmentTreeStorage().save(directory, self.make_tree())
            self.assertTrue(
                Path(directory, ".pacepilot", "development_tree.json").exists()
            )
            self.assertFalse(
                Path(directory, ".pacepilot", "project.json").exists()
            )

    def test_schema_version_is_validated(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = DevelopmentTreeStorage()
            storage.save(directory, self.make_tree())
            path = Path(directory, ".pacepilot", "development_tree.json")
            text = path.read_text(encoding="utf-8").replace(
                '"schema_version": 1',
                '"schema_version": 999',
            )
            path.write_text(text, encoding="utf-8")

            with self.assertRaises(ValueError):
                storage.load(directory)


if __name__ == "__main__":
    unittest.main()
