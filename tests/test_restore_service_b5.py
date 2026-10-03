import tempfile
import unittest
from pathlib import Path

from application.models import ProjectGoal, ProjectModel
from application.restore_service import ProjectRestoreState, RestoreService


class TestRestoreServiceB5(unittest.TestCase):
    def test_restore_project_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = ProjectModel(
                project_id="p1",
                goal=ProjectGoal(text="test goal"),
            )

            from application.project_storage import ProjectStorage
            ProjectStorage().save(project, root)

            restored = RestoreService().restore(root)

            self.assertIsInstance(restored, ProjectRestoreState)
            self.assertEqual(restored.project.project_id, "p1")
            self.assertEqual(restored.project.goal.text, "test goal")
            self.assertIsNone(restored.workflow)
            self.assertEqual(restored.history, ())
            self.assertIsNone(restored.context)

    def test_restore_uses_existing_optional_state_only(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            project = ProjectModel(
                project_id="p2",
                goal=ProjectGoal(text="persistent"),
            )

            from application.project_storage import ProjectStorage
            ProjectStorage().save(project, root)

            service = RestoreService()

            self.assertTrue(service.has_project(root))
            self.assertFalse(service.has_workflow(root))
            self.assertFalse(service.has_history(root))
            self.assertFalse(service.has_context(root))

            restored = service.restore(root)

            self.assertIsNone(restored.workflow)
            self.assertEqual(restored.history, ())
            self.assertIsNone(restored.context)

    def test_missing_project_is_not_fabricated(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            with self.assertRaises(FileNotFoundError):
                RestoreService().restore(root)

    def test_context_retrieval_delegates_to_persistence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            service = RestoreService()

            with self.assertRaises(FileNotFoundError):
                service.load_context(root)


if __name__ == "__main__":
    unittest.main()
