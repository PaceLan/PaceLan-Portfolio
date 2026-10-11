import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from agent_workflow.workflow_plan import WorkflowStep
from application.bootstrap import ApplicationBootstrap
from application.vscode_terminal_executor import VSCodeTerminalCommandExecutor


class TerminalExecutionChainC658Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.runtime = ApplicationBootstrap.create(Path(self.temp_dir.name))
        self.service = self.runtime.execution_service

    def tearDown(self):
        self.service._executor.shutdown(wait=True)
        self.temp_dir.cleanup()

    def test_explicit_command_routes_to_terminal_executor(self):
        executor = Mock(return_value="exit code 0")
        self.service._terminal_command_executor = executor
        step = WorkflowStep(
            operation="run-tests",
            action=Mock(side_effect=AssertionError("callback must not run")),
            terminal_command="python -m unittest",
        )

        result = self.service._controlled_step(step).action()

        self.assertEqual(result, "exit code 0")
        executor.assert_called_once_with("python -m unittest")

    def test_explicit_command_without_executor_fails_closed(self):
        self.service._terminal_command_executor = None
        step = WorkflowStep(
            operation="run-tests",
            action=Mock(),
            terminal_command="python -m unittest",
        )

        with self.assertRaisesRegex(RuntimeError, "no terminal executor"):
            self.service._controlled_step(step).action()

    def test_regular_callback_does_not_use_terminal_executor(self):
        executor = Mock(return_value="unexpected")
        callback = Mock(return_value="callback-result")
        self.service._terminal_command_executor = executor
        step = WorkflowStep(operation="ordinary", action=callback)

        result = self.service._controlled_step(step).action()

        self.assertEqual(result, "callback-result")
        callback.assert_called_once_with()
        executor.assert_not_called()

    def test_bootstrap_does_not_execute_terminal_command(self):
        with patch.object(
            VSCodeTerminalCommandExecutor,
            "execute",
            autospec=True,
        ) as execute:
            runtime = ApplicationBootstrap.create(Path(self.temp_dir.name))
            execute.assert_not_called()
            runtime.execution_service._executor.shutdown(wait=True)


if __name__ == "__main__":
    unittest.main()
