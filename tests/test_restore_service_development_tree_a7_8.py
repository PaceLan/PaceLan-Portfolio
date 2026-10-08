import tempfile
import unittest
from pathlib import Path

from application.development_tree import (
    DevelopmentNodeStatus,
    DevelopmentNodeType,
    DevelopmentTreeNode,
)
from application.development_tree_storage import DevelopmentTreeStorage
from application.models import ProjectModel
from application.project_storage import ProjectStorage
from application.restore_service import RestoreService


class RestoreServiceDevelopmentTreeA78Tests(unittest.TestCase):
    def make_project(self) -> ProjectModel:
        return ProjectModel(project_id="project-1")

    def make_node(self) -> DevelopmentTreeNode:
        return DevelopmentTreeNode(
            node_id="module-a",
            project_id="project-1",
            node_key="A7.8",
            node_type=DevelopmentNodeType.MODULE,
            status=DevelopmentNodeStatus.COMPLETED,
            title="Development Tree Recovery",
            started_at="2026-10-08T10:00:00+00:00",
            completed_at="2026-10-08T11:00:00+00:00",
            summary="恢复开发树",
        )

    def prepare_project(self, path: Path) -> ProjectModel:
        project = self.make_project()
        ProjectStorage().save(project, path, name="Test Project")
        return project

    def test_restore_includes_persisted_development_tree(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            project = self.prepare_project(path)
            node = self.make_node()
            DevelopmentTreeStorage().save(str(path), (node,))

            restored = RestoreService().restore(str(path))

            self.assertEqual(restored.project, project)
            self.assertEqual(restored.development_tree, (node,))

    def test_missing_development_tree_restores_empty(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            self.prepare_project(path)

            restored = RestoreService().restore(str(path))

            self.assertEqual(restored.development_tree, ())
            self.assertFalse(RestoreService().has_development_tree(str(path)))

    def test_load_development_tree_returns_persisted_nodes(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            node = self.make_node()
            DevelopmentTreeStorage().save(str(path), (node,))

            self.assertEqual(
                RestoreService().load_development_tree(str(path)),
                (node,),
            )


if __name__ == "__main__":
    unittest.main()
