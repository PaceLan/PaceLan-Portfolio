import unittest
from datetime import datetime

from application.execution_checkpoint import (
    CHECKPOINT_EVENTS,
    checkpoint,
    checkpoint_if_needed,
)
from application.execution_context import ExecutionContext


class TestExecutionCheckpoint(unittest.TestCase):

    def _context(self):
        return ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            run_id="run-1",
            step_id="step-1",
        )

    def test_checkpoint_increments_sequence(self):
        context = self._context()

        updated = checkpoint(context, "EXECUTION_STARTED")

        self.assertEqual(context.checkpoint_sequence, 0)
        self.assertEqual(updated.checkpoint_sequence, 1)

    def test_checkpoint_records_timestamp(self):
        updated = checkpoint(
            self._context(),
            "EXECUTION_STARTED",
        )

        self.assertIsInstance(updated.checkpointed_at, datetime)

    def test_checkpoint_does_not_mutate_original_context(self):
        context = self._context()

        updated = checkpoint(context, "STEP_STARTED")

        self.assertEqual(context.checkpoint_sequence, 0)
        self.assertEqual(updated.checkpoint_sequence, 1)

    def test_multiple_checkpoints_are_monotonic(self):
        context = self._context()

        first = checkpoint(context, "EXECUTION_STARTED")
        second = checkpoint(first, "STEP_STARTED")
        third = checkpoint(second, "STEP_COMPLETED")

        self.assertEqual(first.checkpoint_sequence, 1)
        self.assertEqual(second.checkpoint_sequence, 2)
        self.assertEqual(third.checkpoint_sequence, 3)

    def test_unsupported_event_is_rejected(self):
        with self.assertRaises(ValueError):
            checkpoint(self._context(), "OUTPUT_RECEIVED")

    def test_empty_event_is_rejected(self):
        with self.assertRaises(ValueError):
            checkpoint(self._context(), "")

    def test_checkpoint_if_needed_skips_non_checkpoint_event(self):
        context = self._context()

        result = checkpoint_if_needed(
            context,
            "OUTPUT_RECEIVED",
        )

        self.assertIs(result, context)

    def test_checkpoint_if_needed_processes_checkpoint_event(self):
        context = self._context()

        result = checkpoint_if_needed(
            context,
            "STEP_COMPLETED",
        )

        self.assertEqual(result.checkpoint_sequence, 1)

    def test_checkpoint_events_are_explicit(self):
        self.assertIn("EXECUTION_STARTED", CHECKPOINT_EVENTS)
        self.assertIn("STEP_COMPLETED", CHECKPOINT_EVENTS)
        self.assertNotIn("OUTPUT_RECEIVED", CHECKPOINT_EVENTS)


if __name__ == "__main__":
    unittest.main()
