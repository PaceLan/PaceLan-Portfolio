import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from application.workspace import ApplicationTreeNode
from ui.controller import ApplicationController, ProjectContext


class UiControllerTests(unittest.TestCase):
    def test_controller_starts_with_clean_state(self) -> None:
        controller = ApplicationController()

        self.assertEqual(
            controller.project_context,
            ProjectContext(None, None, False, False),
        )

        state = controller.initial_state()

        self.assertEqual(state.status, "Ready")
        self.assertFalse(state.tree.loaded)
        self.assertIsNone(state.selected_file.path)
        self.assertFalse(state.viewer.loaded)

    def test_open_project_delegates_to_project_manager(self) -> None:
        project_manager = Mock()
        project_manager.get_project_info.return_value = {
            "project_name": "Demo",
            "project_path": Path("C:/Demo"),
            "exists": True,
            "is_directory": True,
        }
        controller = ApplicationController(project_manager=project_manager)

        context = controller.open_project("C:/Demo")

        project_manager.open_project.assert_called_once_with("C:/Demo")
        project_manager.get_project_info.assert_called_once_with()
        self.assertEqual(context.name, "Demo")
        self.assertTrue(context.is_directory)

    def test_tree_data_is_delegated_to_injected_provider(self) -> None:
        root_node = ApplicationTreeNode(
            "Demo",
            Path("C:/Demo"),
            True,
        )
        tree_provider = Mock()

        from core.project_tree import ProjectTreeNode

        core_root = ProjectTreeNode(
            "Demo",
            Path("C:/Demo"),
            True,
        )
        tree_provider.build_tree.return_value = core_root

        project_manager = Mock()
        project_manager.get_project_info.return_value = {
            "project_name": "Demo",
            "project_path": Path("C:/Demo"),
            "exists": True,
            "is_directory": True,
        }

        controller = ApplicationController(
            project_manager,
            tree_provider,
        )
        controller.open_project("C:/Demo")

        result = controller.get_project_tree()

        self.assertEqual(result, root_node)
        tree_provider.build_tree.assert_called_once_with()

    def test_tree_requires_valid_project_context(self) -> None:
        controller = ApplicationController()

        with self.assertRaises(ValueError):
            controller.get_project_tree()

    def test_valid_file_selection_delegates_to_file_reader(self) -> None:
        project_manager = Mock()
        project_manager.get_project_info.return_value = {
            "project_name": "Demo",
            "project_path": Path("C:/Demo"),
            "exists": True,
            "is_directory": True,
        }

        file_reader = Mock()
        file_reader.read_file.return_value = "print('demo')"

        controller = ApplicationController(
            project_manager=project_manager,
            file_reader=file_reader,
        )
        controller.open_project("C:/Demo")

        result = controller.select_file("src/demo.py")

        file_reader.read_file.assert_called_once_with("src/demo.py")
        self.assertTrue(result.success)
        self.assertEqual(result.path, "src/demo.py")
        self.assertEqual(result.contents, "print('demo')")

    def test_invalid_file_selection_returns_safe_error(self) -> None:
        project_manager = Mock()
        project_manager.get_project_info.return_value = {
            "project_name": "Demo",
            "project_path": Path("C:/Demo"),
            "exists": True,
            "is_directory": True,
        }

        file_reader = Mock()
        file_reader.read_file.side_effect = FileNotFoundError(
            "File does not exist"
        )

        controller = ApplicationController(
            project_manager=project_manager,
            file_reader=file_reader,
        )
        controller.open_project("C:/Demo")

        result = controller.select_file("missing.py")

        self.assertFalse(result.success)
        self.assertEqual(result.path, "missing.py")
        self.assertEqual(result.error, "File does not exist")

    def test_controller_does_not_require_real_gui_or_filesystem(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_root:
            project_manager = Mock()
            project_manager.get_project_info.return_value = {
                "project_name": "Temporary",
                "project_path": Path(temporary_root),
                "exists": True,
                "is_directory": True,
            }

            controller = ApplicationController(
                project_manager=project_manager
            )

            controller.open_project(temporary_root)

            self.assertEqual(
                controller.project_context.path,
                Path(temporary_root),
            )

            state = controller.initial_state()

            self.assertEqual(
                state.status,
                "Ready",
            )
            self.assertFalse(
                state.tree.loaded,
            )
            self.assertIsNone(
                state.selected_file.path,
            )
            self.assertFalse(
                state.viewer.loaded,
            )


if __name__ == "__main__":
    unittest.main()
