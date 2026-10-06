import tempfile
import unittest

from application.execution_context import ExecutionContext
from application.execution_context_restore import (
    ExecutionContextRestoreService,
)
from application.execution_context_storage import ExecutionContextStorage


class TestExecutionContextRestore(unittest.TestCase):

    def _context(self, process=True, terminal=True):
        return ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            run_id="run-1",
            step_id="step-1",
            process_id=1234 if process else None,
            process_state="RUNNING" if process else None,
            terminal_id="terminal-1" if terminal else None,
            terminal_session_id="session-1" if terminal else None,
            terminal_state="RUNNING" if terminal else None,
            execution_state="RUNNING",
            recoverability="RECOVERABLE",
        )

    def test_restore_returns_persisted_context(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ExecutionContextStorage(directory)
            context = self._context()

            storage.save(context)

            restored = ExecutionContextRestoreService(
                storage
            ).restore()

            self.assertIsNotNone(restored)
            self.assertEqual(
                restored.context.project_id,
                "project-1",
            )
            self.assertEqual(
                restored.context.run_id,
                "run-1",
            )

    def test_process_requires_revalidation_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ExecutionContextStorage(directory)
            storage.save(self._context(process=True, terminal=False))

            restored = ExecutionContextRestoreService(
                storage
            ).restore()

            self.assertTrue(
                restored.process_revalidation_required
            )
            self.assertFalse(
                restored.terminal_revalidation_required
            )

    def test_terminal_requires_revalidation_after_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ExecutionContextStorage(directory)
            storage.save(self._context(process=False, terminal=True))

            restored = ExecutionContextRestoreService(
                storage
            ).restore()

            self.assertFalse(
                restored.process_revalidation_required
            )
            self.assertTrue(
                restored.terminal_revalidation_required
            )

    def test_restore_marks_context_for_revalidation(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ExecutionContextStorage(directory)
            storage.save(self._context())

            restored = ExecutionContextRestoreService(
                storage
            ).restore()

            self.assertEqual(
                restored.context.recoverability,
                "REVALIDATION_REQUIRED",
            )

    def test_missing_context_returns_none(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ExecutionContextStorage(directory)

            restored = ExecutionContextRestoreService(
                storage
            ).restore()

            self.assertIsNone(restored)

    def test_restore_does_not_claim_process_is_alive(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ExecutionContextStorage(directory)
            storage.save(self._context())

            restored = ExecutionContextRestoreService(
                storage
            ).restore()

            self.assertTrue(
                restored.process_revalidation_required
            )
            self.assertEqual(
                restored.context.process_state,
                "RUNNING",
            )


if __name__ == "__main__":
    unittest.main()
