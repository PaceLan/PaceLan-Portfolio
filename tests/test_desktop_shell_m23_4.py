import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from application.bootstrap import ApplicationRuntime, BootstrapState
from ui import app_entry


class DesktopShellM234Tests(unittest.TestCase):

    def test_create_runtime_delegates_to_application_bootstrap(self):
        expected = MagicMock(spec=ApplicationRuntime)

        with patch(
            "ui.app_entry.ApplicationBootstrap.create",
            return_value=expected,
        ) as create:
            result = app_entry.create_runtime(Path("."))

        self.assertIs(result, expected)
        create.assert_called_once_with(
            Path("."),
            agent_service=None,
        )

    def test_create_app_uses_bootstrapped_agent_service(self):
        root = MagicMock()
        agent_service = MagicMock()
        runtime = MagicMock()
        runtime.agent_service = agent_service

        with patch(
            "ui.app_entry.create_runtime",
            return_value=runtime,
        ), patch(
            "ui.app_entry._create_app",
            return_value=MagicMock(),
        ) as create:
            result = app_entry.create_app(
                root,
                project_root=Path("."),
            )

        self.assertIsNotNone(result)
        create.assert_called_once_with(
            root,
            project_root=Path("."),
            controller=None,
            agent_service=agent_service,
        )

    def test_create_app_without_project_root_preserves_agent_service(self):
        root = MagicMock()
        agent_service = MagicMock()

        with patch(
            "ui.app_entry._create_app",
            return_value=MagicMock(),
        ) as create:
            app_entry.create_app(
                root,
                agent_service=agent_service,
            )

        create.assert_called_once_with(
            root,
            project_root=None,
            controller=None,
            agent_service=agent_service,
        )

    def test_main_creates_tk_root_and_enters_mainloop(self):
        root = MagicMock()
        runtime = MagicMock()
        runtime.agent_service = MagicMock()

        with patch("ui.app_entry.tk.Tk", return_value=root), patch(
            "ui.app_entry.create_runtime",
            return_value=runtime,
        ) as create_runtime, patch(
            "ui.app_entry.create_app"
        ) as create:
            app_entry.main()

        create_runtime.assert_called_once()
        create.assert_called_once_with(
            root,
            agent_service=runtime.agent_service,
        )
        root.mainloop.assert_called_once_with()

    def test_main_reports_project_startup_failure(self):
        root = MagicMock()

        with patch("ui.app_entry.tk.Tk", return_value=root), patch(
            "ui.app_entry.create_app",
            side_effect=ValueError("invalid project"),
        ), patch("ui.app_entry.messagebox.showerror") as showerror:
            app_entry.main()

        showerror.assert_called_once_with(
            "PacePilot could not start",
            "invalid project",
            parent=root,
        )
        root.destroy.assert_called_once_with()

    def test_bootstrap_ready_state_is_the_desktop_runtime_boundary(self):
        self.assertEqual(BootstrapState.READY.value, "ready")


if __name__ == "__main__":
    unittest.main()
