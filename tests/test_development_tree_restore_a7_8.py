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


class DevelopmentTreeRestoreA78Tests(unittest.TestCase):
    def make_project(self) -> ProjectModel:
        return ProjectModel(project_id="project-1")

    def make_node(self):
        return DevelopmentTreeNode(
            node_id="a7.8-node",
            project_id="project-1",
            node_key="A7.8",
            node_type=DevelopmentNodeType.MODULE,
            status=DevelopmentNodeStatus.COMPLETED,
            title="Development Tree Recovery",
            started_at="2026-10-08T10:00:00+00:00",
            completed_at="2026-10-08T11:00:00+00:00",
            task_id="task-1",
            run_id="run-1",
            history_id="history-1",
            summary="恢复开发树",
        )

    def prepare_project(self, project_path: Path) -> ProjectModel:
        project = self.make_project()
        ProjectStorage().save(project, project_path, name="Test Project")
        return project

    def test_restore_includes_development_tree(self):
        with tempfile.TemporaryDirectory() as path:
            project_path = Path(path)
            project = self.prepare_project(project_path)
            node = self.make_node()
            DevelopmentTreeStorage().save(project_path, (node,))

            restored = RestoreService().restore(project_path)

            self.assertEqual(restored.project, project)
            self.assertEqual(restored.development_tree, (node,))

    def test_missing_development_tree_restores_as_empty(self):
        with tempfile.TemporaryDirectory() as path:
            project_path = Path(path)
            self.prepare_project(project_path)

            restored = RestoreService().restore(project_path)

            self.assertEqual(restored.development_tree, ())

    def test_restore_service_exposes_tree_loader(self):
        with tempfile.TemporaryDirectory() as path:
            project_path = Path(path)
            self.prepare_project(project_path)
            node = self.make_node()
            DevelopmentTreeStorage().save(project_path, (node,))

            service = RestoreService()

            self.assertTrue(service.has_development_tree(project_path))
            self.assertEqual(
                service.load_development_tree(project_path),
                (node,),
            )


if __name__ == "__main__":
    unittest.main()
