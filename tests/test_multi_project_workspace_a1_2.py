import tempfile
import unittest

from application.multi_project_workspace import MultiProjectWorkspaceService


class TestMultiProjectWorkspaceService(unittest.TestCase):

    def test_open_project_switches_registry_and_workspace(self):
        with tempfile.TemporaryDirectory() as first, \
             tempfile.TemporaryDirectory() as second:
            service = MultiProjectWorkspaceService()

            service.register_project("alpha", first)
            service.register_project("beta", second)

            info = service.open_project("beta")

            self.assertEqual(
                service.registry.active_project_id,
                "beta",
            )
            self.assertEqual(
                service.workspace.project_path,
                service.active_project.path,
            )
            self.assertEqual(info["project_path"], service.active_project.path)

    def test_switch_project_changes_active_workspace(self):
        with tempfile.TemporaryDirectory() as first, \
             tempfile.TemporaryDirectory() as second:
            service = MultiProjectWorkspaceService()

            service.register_project("alpha", first)
            service.register_project("beta", second)

            service.open_project("alpha")
            service.switch_project("beta")

            self.assertEqual(
                service.registry.active_project_id,
                "beta",
            )
            self.assertEqual(
                service.workspace.project_path,
                service.active_project.path,
            )

    def test_remove_active_project_closes_workspace(self):
        with tempfile.TemporaryDirectory() as project_path:
            service = MultiProjectWorkspaceService()

            service.register_project("alpha", project_path)
            service.open_project("alpha")
            service.remove_project("alpha")

            self.assertIsNone(service.registry.active_project_id)
            self.assertIsNone(service.workspace.project_path)


if __name__ == "__main__":
    unittest.main()
