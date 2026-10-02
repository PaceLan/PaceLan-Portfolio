import tempfile
import unittest
from pathlib import Path

from ui.controller import ApplicationController


class TestApplicationControllerA1_3(unittest.TestCase):

    def test_open_project_registers_project(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            project_path = Path(temp_dir) / "ProjectAlpha"
            project_path.mkdir()

            controller = ApplicationController()
            context = controller.open_project(project_path)

            self.assertEqual(context.path, project_path.resolve())
            self.assertEqual(controller.active_project.path, project_path.resolve())
            self.assertEqual(len(controller.list_projects()), 1)

    def test_multiple_projects_can_be_switched(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            alpha = root / "ProjectAlpha"
            beta = root / "ProjectBeta"
            alpha.mkdir()
            beta.mkdir()

            controller = ApplicationController()
            controller.open_project(alpha)
            controller.open_project(beta)

            projects = controller.list_projects()
            self.assertEqual(len(projects), 2)
            self.assertEqual(controller.active_project.path, beta.resolve())

            alpha_id = next(
                project.project_id
                for project in projects
                if project.path == alpha.resolve()
            )

            context = controller.switch_project(alpha_id)

            self.assertEqual(context.path, alpha.resolve())
            self.assertEqual(controller.active_project.path, alpha.resolve())


if __name__ == "__main__":
    unittest.main()
