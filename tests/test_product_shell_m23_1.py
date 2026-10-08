import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import main
from ui import app_entry


class TestM23_1ProductShellEntry(unittest.TestCase):

    def test_root_main_without_legacy_argument_starts_desktop(self):
        with patch("main._desktop_main") as desktop_main:
            main.main()

        desktop_main.assert_called_once_with()

    def test_create_app_delegates_to_ui_factory(self):
        root = MagicMock()
        controller = MagicMock()
        agent_service = MagicMock()
        expected = MagicMock()

        with patch.object(app_entry, "_create_app", return_value=expected) as factory:
            result = app_entry.create_app(
                root,
                project_root=Path("project"),
                controller=controller,
                agent_service=agent_service,
            )

        self.assertIs(result, expected)
        factory.assert_called_once_with(
            root,
            project_root=Path("project"),
            controller=controller,
            agent_service=agent_service,
            execution_service=None,
        )

    def test_create_app_signature_preserves_shell_dependencies(self):
        self.assertIn("root", app_entry.create_app.__annotations__)
        self.assertIn("project_root", app_entry.create_app.__annotations__)

    def test_main_starts_startup_coordinator_and_mainloop(self):
        root = MagicMock()
        coordinator = MagicMock()

        with patch.object(app_entry.tk, "Tk", return_value=root) as tk_factory, \
             patch.object(
                 app_entry,
                 "StartupCoordinator",
                 return_value=coordinator,
             ) as coordinator_factory:
            app_entry.main()

        tk_factory.assert_called_once_with()
        coordinator_factory.assert_called_once()

        args, kwargs = coordinator_factory.call_args
        self.assertEqual(args[0], root)

        runtime_root = Path(kwargs["runtime_root"])
        self.assertEqual(runtime_root.name, "runtime")
        self.assertEqual(runtime_root.parent.name, "PacePilot")
        self.assertEqual(kwargs["greeting_resolver"], app_entry.resolve_daily_greeting)

        coordinator.start.assert_called_once_with()
        root.mainloop.assert_called_once_with()


class TestM23_1RootEntry(unittest.TestCase):

    def test_main_module_delegates_to_product_shell(self):
        source = Path("main.py").read_text(encoding="utf-8-sig")

        self.assertIn("from ui.app_entry import main", source)
        self.assertIn("if __name__ == \"__main__\":", source)
        self.assertIn("    main()", source)

    def test_root_entry_has_no_legacy_core_imports(self):
        source = Path("main.py").read_text(encoding="utf-8-sig")

        forbidden = (
            "from core.",
            "import core.",
            "ProjectManager",
            "ProjectTree",
            "FileReader",
            "FileWriter",
        )

        for token in forbidden:
            self.assertNotIn(token, source)


if __name__ == "__main__":
    unittest.main()
