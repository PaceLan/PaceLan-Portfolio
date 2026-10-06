import unittest

from application.execution_context import ExecutionContext
from application.process_context_binding import (
    ProcessContextBinding,
    bind_process_context,
)
from application.process_lifecycle import (
    ProcessLifecycleState,
    ProcessSnapshot,
)


class TestProcessContextBinding(unittest.TestCase):

    def _snapshot(self):
        return ProcessSnapshot(
            process_id=1234,
            state=ProcessLifecycleState.RUNNING,
        )

    def _context(self):
        return ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            run_id="run-1",
            step_id="step-1",
            process_id=1234,
            process_state=ProcessLifecycleState.RUNNING.value,
        )

    def test_binding_preserves_snapshot_and_context(self):
        snapshot = self._snapshot()
        context = self._context()

        binding = bind_process_context(snapshot, context)

        self.assertIs(binding.snapshot, snapshot)
        self.assertIs(binding.context, context)

    def test_binding_exposes_process_identity(self):
        binding = bind_process_context(
            self._snapshot(),
            self._context(),
        )

        self.assertEqual(binding.process_id, 1234)
        self.assertEqual(
            binding.process_state,
            ProcessLifecycleState.RUNNING.value,
        )
        self.assertEqual(binding.run_id, "run-1")
        self.assertEqual(binding.task_id, "task-1")

    def test_process_id_mismatch_is_rejected(self):
        context = ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            run_id="run-1",
            step_id="step-1",
            process_id=9999,
            process_state=ProcessLifecycleState.RUNNING.value,
        )

        with self.assertRaises(ValueError):
            ProcessContextBinding(self._snapshot(), context)

    def test_process_state_mismatch_is_rejected(self):
        context = ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            run_id="run-1",
            step_id="step-1",
            process_id=1234,
            process_state=ProcessLifecycleState.EXITED.value,
        )

        with self.assertRaises(ValueError):
            ProcessContextBinding(self._snapshot(), context)

    def test_binding_is_immutable(self):
        binding = bind_process_context(
            self._snapshot(),
            self._context(),
        )

        with self.assertRaises(AttributeError):
            binding.snapshot = self._snapshot()


if __name__ == "__main__":
    unittest.main()
