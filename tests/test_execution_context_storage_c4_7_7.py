import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from application.execution_checkpoint import checkpoint
from application.execution_context import ExecutionContext
from application.execution_context_storage import ExecutionContextStorage


class TestExecutionContextStorage(unittest.TestCase):

    def _context(self, sequence=0):
        return ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            run_id="run-1",
            step_id="step-1",
            execution_state="RUNNING",
            checkpoint_sequence=sequence,
            checkpointed_at=(
                datetime.now(timezone.utc) if sequence else None
            ),
        )

    def test_save_and_load_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ExecutionContextStorage(directory)
            context = self._context()

            storage.save(context)
            restored = storage.load()

            self.assertEqual(restored, context)

    def test_update_replaces_context_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ExecutionContextStorage(directory)
            first = checkpoint(
                self._context(),
                "EXECUTION_STARTED",
            )
            second = checkpoint(
                first,
                "STEP_STARTED",
            )

            storage.update(first)
            storage.update(second)

            restored = storage.load()

            self.assertEqual(restored.checkpoint_sequence, 2)

    def test_stale_context_cannot_replace_newer_context(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ExecutionContextStorage(directory)
            current = checkpoint(
                self._context(),
                "EXECUTION_STARTED",
            )
            stale = self._context()

            storage.update(current)

            with self.assertRaises(ValueError):
                storage.update(stale)

            restored = storage.load()
            self.assertEqual(restored.checkpoint_sequence, 1)

    def test_storage_uses_pacepilot_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ExecutionContextStorage(directory)

            self.assertEqual(
                storage.storage_path,
                Path(directory)
                / ".pacepilot"
                / "execution_context.json",
            )

    def test_missing_context_returns_none(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ExecutionContextStorage(directory)

            self.assertIsNone(storage.load())

    def test_schema_version_is_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = ExecutionContextStorage(directory)
            storage.save(self._context())

            payload = storage.storage_path.read_text(
                encoding="utf-8"
            )

            self.assertIn('"schema_version": 1', payload)


if __name__ == "__main__":
    unittest.main()
