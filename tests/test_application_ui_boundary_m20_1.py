"""M20.1 Application-to-UI boundary tests."""

import unittest
from pathlib import Path
from unittest.mock import Mock

from application.workspace import ProjectWorkspaceService
from application.workspace import ApplicationTreeNode
from ui.controller import ApplicationController, ProjectContext


class M201ApplicationUiBoundaryTests(unittest.TestCase):

    def test_controller_uses_application_workspace(self):
        workspace = Mock(spec=ProjectWorkspaceService)
        workspace.open_project.return_value = {
            "project_name": "Demo",
            "project_path": Path("C:/Demo"),
            "exists": True,
            "is_directory": True,
        }

        controller = ApplicationController(workspace=workspace)

        context = controller.open_project("C:/Demo")

        workspace.open_project.assert_called_once_with("C:/Demo")
        self.assertEqual(context.name, "Demo")

    def test_controller_tree_delegates_to_application_boundary(self):
        workspace = Mock(spec=ProjectWorkspaceService)
        workspace.open_project.return_value = {
            "project_name": "Demo",
            "project_path": Path("C:/Demo"),
            "exists": True,
            "is_directory": True,
        }

        root = ApplicationTreeNode(
            "Demo",
            Path("C:/Demo"),
            True,
        )
        workspace.build_tree_model.return_value = root

        controller = ApplicationController(workspace=workspace)
        controller.open_project("C:/Demo")

        self.assertEqual(controller.get_project_tree(), root)
        workspace.build_tree_model.assert_called_once_with()

    def test_controller_file_selection_uses_application_boundary(self):
        workspace = Mock(spec=ProjectWorkspaceService)
        workspace.open_project.return_value = {
            "project_name": "Demo",
            "project_path": Path("C:/Demo"),
            "exists": True,
            "is_directory": True,
        }
        workspace.read_file.return_value = "print('demo')"

        controller = ApplicationController(workspace=workspace)
        controller.open_project("C:/Demo")

        result = controller.select_file("src/demo.py")

        workspace.read_file.assert_called_once_with("src/demo.py")
        self.assertTrue(result.success)
        self.assertEqual(result.contents, "print('demo')")

    def test_ui_controller_no_longer_imports_core_services(self):
        source = Path("ui/controller.py").read_text(encoding="utf-8")

        self.assertNotIn(
            "from core.file_reader",
            source,
        )
        self.assertNotIn(
            "from core.project_manager",
            source,
        )


    def test_ui_modules_do_not_import_core(self):
        for relative_path in ("ui/controller.py", "ui/app.py"):
            source = Path(relative_path).read_text(encoding="utf-8")
            self.assertNotIn("from core", source)
            self.assertNotIn("import core", source)
            self.assertNotIn("ProjectTreeNode", source)

    def test_application_workspace_is_importable(self):
        from application.workspace import ProjectWorkspaceService

        self.assertTrue(ProjectWorkspaceService)


if __name__ == "__main__":
    unittest.main()
