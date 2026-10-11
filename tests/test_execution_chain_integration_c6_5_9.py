import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from application.bootstrap import ApplicationBootstrap
from application.models import TaskModel
from agent_workflow.workflow_plan import WorkflowStep


class ExecutionChainIntegrationC659Tests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.runtime = ApplicationBootstrap.create(Path(self.temp_dir.name))
        self.service = self.runtime.execution_service
        self.task = TaskModel(
            task_id="c659-task",
            project_id="c659-project",
            description="Verify execution chain",
        )

    def tearDown(self):
        self.service._executor.shutdown(wait=True)
        self.temp_dir.cleanup()

    def test_run_dispatches_explicit_command_through_agent_workflow(self):
        executor = Mock(return_value="terminal exit code 0")
        callback = Mock(side_effect=AssertionError("wrong execution path"))
        self.service._terminal_command_executor = executor
        step = WorkflowStep(
            operation="execute-terminal-command",
            action=callback,
            step_id="c659-terminal-step",
            terminal_command="python -c \"print(123)\"",
        )

        result = self.service.run(self.task, (step,))

        executor.assert_called_once_with('python -c "print(123)"')
        callback.assert_not_called()
        self.assertEqual(result.task.task_id, self.task.task_id)
        self.assertIsNotNone(result.result)
        self.assertIsNotNone(result.verification)

    def test_run_keeps_regular_callback_on_workflow_path(self):
        executor = Mock(return_value="unexpected")
        callback = Mock(return_value="ordinary result")
        self.service._terminal_command_executor = executor
        step = WorkflowStep(
            operation="ordinary-callback",
            action=callback,
            step_id="c659-callback-step",
        )

        result = self.service.run(self.task, (step,))

        callback.assert_called_once_with()
        executor.assert_not_called()
        self.assertEqual(result.task.task_id, self.task.task_id)

    def test_missing_executor_produces_failed_workflow_result(self):
        self.service._terminal_command_executor = None
        step = WorkflowStep(
            operation="terminal-without-executor",
            action=Mock(),
            step_id="c659-no-executor",
            terminal_command="python -c \"print(123)\"",
        )

        result = self.service.run(self.task, (step,))

        status = result.result.status
        status_value = getattr(status, "value", status)
        self.assertEqual(str(status_value).upper(), "FAILED")
        self.assertFalse(result.verification.verified)


if __name__ == "__main__":
    unittest.main()
