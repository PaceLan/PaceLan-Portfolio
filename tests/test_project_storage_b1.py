import tempfile
import unittest
from pathlib import Path

from application.models import ProjectGoal, ProjectModel
from application.project_storage import ProjectStorage
from application.project_registry import ProjectRegistry


class ProjectStorageB1Tests(unittest.TestCase):

    def test_project_model_survives_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            storage = ProjectStorage()

            storage.save(
                ProjectModel(
                    project_id="project-001",
                    goal=ProjectGoal("Build PacePilot"),
                ),
                path,
            )

            restored = ProjectStorage().load(path)

            self.assertEqual(restored.project_id, "project-001")
            self.assertEqual(restored.goal.text, "Build PacePilot")

    def test_project_state_survives_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)
            storage = ProjectStorage()

            storage.save(
                ProjectModel(project_id="project-001"),
                path,
                current_phase="B1",
                current_task="task-001",
                next_task="task-002",
                completed=False,
                blocked=True,
            )

            state = ProjectStorage().load_state(path)

            self.assertEqual(state["current_phase"], "B1")
            self.assertEqual(state["current_task"], "task-001")
            self.assertEqual(state["next_task"], "task-002")
            self.assertFalse(state["completed"])
            self.assertTrue(state["blocked"])

    def test_registry_survives_restart(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            first = root / "first"
            second = root / "second"
            first.mkdir()
            second.mkdir()

            registry_file = root / "registry.json"

            registry = ProjectRegistry(registry_file)
            registry.register_project("alpha", first)
            registry.register_project("beta", second)
            registry.switch_project("beta")
            registry.save()

            restored = ProjectRegistry(registry_file)

            self.assertEqual(
                tuple(
                    project.project_id
                    for project in restored.list_projects()
                ),
                ("alpha", "beta"),
            )
            self.assertEqual(
                restored.get_project("alpha").path,
                first.resolve(),
            )
            self.assertEqual(
                restored.active_project_id,
                "beta",
            )


if __name__ == "__main__":
    unittest.main()
