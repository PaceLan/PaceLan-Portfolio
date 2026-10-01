import unittest
from unittest.mock import Mock

from ui.agent_panel import AgentInteractionPanel


class AgentPanelM233RuntimeControlTests(unittest.TestCase):
    def test_panel_exposes_runtime_controls(self):
        self.assertTrue(hasattr(AgentInteractionPanel, "_on_start"))
        self.assertTrue(hasattr(AgentInteractionPanel, "_on_pause"))
        self.assertTrue(hasattr(AgentInteractionPanel, "_on_resume"))
        self.assertTrue(hasattr(AgentInteractionPanel, "_on_terminate"))
        self.assertTrue(hasattr(AgentInteractionPanel, "set_controller"))

    def test_controller_runtime_entrypoints_are_delegated(self):
        controller = Mock()

        panel = object.__new__(AgentInteractionPanel)
        panel.controller = controller

        panel._current_state = Mock()
        panel._current_state.task = Mock()
        panel._current_state.plan.steps = ("step-1", "step-2")

        controller.agent_runtime_status.return_value = "running"

        panel._on_start()
        controller.start_agent_task.assert_called_once_with(
            panel._current_state.task,
            ("step-1", "step-2"),
        )

        panel._on_pause()
        controller.pause_agent.assert_called_once_with()

        panel._on_resume()
        controller.resume_agent.assert_called_once_with()

        panel._on_terminate()
        controller.terminate_agent.assert_called_once_with()

    def test_runtime_status_is_read_from_controller(self):
        controller = Mock()
        controller.agent_runtime_status.return_value = "paused"

        panel = object.__new__(AgentInteractionPanel)
        panel.controller = controller
        panel.runtime_status = Mock()

        panel._refresh_runtime_status()

        controller.agent_runtime_status.assert_called_once_with()
        panel.runtime_status.configure.assert_called_once_with(
            text="Runtime: paused"
        )


if __name__ == "__main__":
    unittest.main()
