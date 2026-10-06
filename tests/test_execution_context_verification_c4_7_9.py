import tempfile
import unittest

from application.execution_context import ExecutionContext
from application.execution_context_restore import (
    ExecutionContextRestoreService,
)
from application.execution_context_storage import ExecutionContextStorage
from application.execution_context_verification import (
    verify_execution_context,
)


class TestExecutionContextVerification(unittest.TestCase):

    def _restore(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ExecutionContextStorage(directory)
            storage.save(
                ExecutionContext(
                    project_id="project-1",
                    task_id="task-1",
                    run_id="run-1",
                    step_id="step-1",
                    process_id=1234,
                    process_state="RUNNING",
                    terminal_id="terminal-1",
                    terminal_session_id="session-1",
                    terminal_state="RUNNING",
                    execution_state="RUNNING",
                    recoverability="RECOVERABLE",
                    checkpoint_sequence=3,
                )
            )

            return ExecutionContextRestoreService(
                storage
            ).restore()

    def test_valid_restored_context(self):
        restored = self._restore()

        result = verify_execution_context(restored)

        self.assertTrue(result.valid)
        self.assertEqual(
            result.reason,
            "execution context is structurally valid",
        )

    def test_process_revalidation_is_preserved(self):
        restored = self._restore()

        result = verify_execution_context(restored)

        self.assertTrue(
            result.requires_process_revalidation
        )

    def test_terminal_revalidation_is_preserved(self):
        restored = self._restore()

        result = verify_execution_context(restored)

        self.assertTrue(
            result.requires_terminal_revalidation
        )

    def test_checkpoint_sequence_is_preserved(self):
        restored = self._restore()

        self.assertEqual(
            restored.context.checkpoint_sequence,
            3,
        )

    def test_identity_is_preserved(self):
        restored = self._restore()

        self.assertEqual(
            restored.context.project_id,
            "project-1",
        )
        self.assertEqual(
            restored.context.task_id,
            "task-1",
        )
        self.assertEqual(
            restored.context.run_id,
            "run-1",
        )
        self.assertEqual(
            restored.context.step_id,
            "step-1",
        )

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(TypeError):
            verify_execution_context(None)


if __name__ == "__main__":
    unittest.main()
