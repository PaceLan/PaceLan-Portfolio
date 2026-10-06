import unittest
from datetime import datetime, timezone

from application.execution_context import ExecutionContext


class TestExecutionContext(unittest.TestCase):

    def _context(self):
        return ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            workflow_id="workflow-1",
            run_id="run-1",
            step_id="step-1",
            command_id="command-1",
            process_id=1234,
            process_state="RUNNING",
            terminal_id="terminal-1",
            terminal_session_id="session-1",
            terminal_state="RUNNING",
            execution_state="RUNNING",
            recoverability="RECOVERABLE",
            checkpoint_sequence=3,
            checkpointed_at=datetime.now(timezone.utc),
        )

    def test_model_preserves_execution_identity(self):
        context = self._context()

        self.assertEqual(context.project_id, "project-1")
        self.assertEqual(context.task_id, "task-1")
        self.assertEqual(context.run_id, "run-1")
        self.assertEqual(context.step_id, "step-1")

    def test_model_preserves_process_and_terminal_identity(self):
        context = self._context()

        self.assertEqual(context.process_id, 1234)
        self.assertEqual(context.terminal_id, "terminal-1")
        self.assertEqual(context.terminal_session_id, "session-1")

    def test_model_is_immutable(self):
        context = self._context()

        with self.assertRaises(AttributeError):
            context.run_id = "other-run"

    def test_required_identity_cannot_be_empty(self):
        with self.assertRaises(ValueError):
            ExecutionContext(
                project_id="",
                task_id="task-1",
                run_id="run-1",
                step_id="step-1",
            )

    def test_process_id_must_be_positive(self):
        with self.assertRaises(ValueError):
            ExecutionContext(
                project_id="project-1",
                task_id="task-1",
                run_id="run-1",
                step_id="step-1",
                process_id=0,
            )

    def test_checkpoint_sequence_cannot_be_negative(self):
        with self.assertRaises(ValueError):
            ExecutionContext(
                project_id="project-1",
                task_id="task-1",
                run_id="run-1",
                step_id="step-1",
                checkpoint_sequence=-1,
            )


if __name__ == "__main__":
    unittest.main()
