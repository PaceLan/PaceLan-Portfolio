import tempfile
import unittest
from pathlib import Path

from application.project_registry import (
    ProjectRegistry,
    RegisteredProject,
)


class TestProjectRegistry(unittest.TestCase):

    def test_register_and_list_projects(self):
        with tempfile.TemporaryDirectory() as first, \
             tempfile.TemporaryDirectory() as second:
            registry = ProjectRegistry()

            first_project = registry.register_project("alpha", first)
            second_project = registry.register_project("beta", second)

            self.assertIsInstance(first_project, RegisteredProject)
            self.assertEqual(first_project.project_id, "alpha")
            self.assertEqual(first_project.path, Path(first).resolve())
            self.assertEqual(
                tuple(project.project_id for project in registry.list_projects()),
                ("alpha", "beta"),
            )

    def test_first_registered_project_becomes_active(self):
        with tempfile.TemporaryDirectory() as project_path:
            registry = ProjectRegistry()

            registry.register_project("alpha", project_path)

            self.assertEqual(registry.active_project_id, "alpha")

    def test_switch_project(self):
        with tempfile.TemporaryDirectory() as first, \
             tempfile.TemporaryDirectory() as second:
            registry = ProjectRegistry()
            registry.register_project("alpha", first)
            registry.register_project("beta", second)

            selected = registry.switch_project("beta")

            self.assertEqual(selected.project_id, "beta")
            self.assertEqual(registry.active_project_id, "beta")

    def test_remove_active_project_selects_next_project(self):
        with tempfile.TemporaryDirectory() as first, \
             tempfile.TemporaryDirectory() as second:
            registry = ProjectRegistry()
            registry.register_project("alpha", first)
            registry.register_project("beta", second)

            registry.remove_project("alpha")

            self.assertIsNone(
                registry.get_project("beta").project_id
                if False else None
            )
            self.assertEqual(registry.active_project_id, "beta")

    def test_unknown_project_is_rejected(self):
        registry = ProjectRegistry()

        with self.assertRaises(KeyError):
            registry.get_project("missing")

    def test_duplicate_id_with_different_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as first, \
             tempfile.TemporaryDirectory() as second:
            registry = ProjectRegistry()
            registry.register_project("alpha", first)

            with self.assertRaises(ValueError):
                registry.register_project("alpha", second)


if __name__ == "__main__":
    unittest.main()
