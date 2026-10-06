import unittest

from application.command_context_binding import (
    CommandContextBinding,
    bind_command_context,
)
from application.command_planning import Command
from application.execution_context import ExecutionContext


class TestCommandContextBinding(unittest.TestCase):

    def _command(self):
        return Command(
            task_id="task-1",
            project_id="project-1",
            step_id="step-1",
            operation="run tests",
        )

    def _context(self):
        return ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            run_id="run-1",
            step_id="step-1",
            command_id="command-1",
        )

    def test_binding_preserves_command_and_context(self):
        command = self._command()
        context = self._context()

        binding = bind_command_context(command, context)

        self.assertIs(binding.command, command)
        self.assertIs(binding.context, context)

    def test_binding_exposes_execution_identity(self):
        binding = bind_command_context(
            self._command(),
            self._context(),
        )

        self.assertEqual(binding.command_id, "command-1")
        self.assertEqual(binding.project_id, "project-1")
        self.assertEqual(binding.task_id, "task-1")
        self.assertEqual(binding.step_id, "step-1")
        self.assertEqual(binding.run_id, "run-1")

    def test_project_mismatch_is_rejected(self):
        context = ExecutionContext(
            project_id="project-2",
            task_id="task-1",
            run_id="run-1",
            step_id="step-1",
        )

        with self.assertRaises(ValueError):
            CommandContextBinding(self._command(), context)

    def test_task_mismatch_is_rejected(self):
        context = ExecutionContext(
            project_id="project-1",
            task_id="task-2",
            run_id="run-1",
            step_id="step-1",
        )

        with self.assertRaises(ValueError):
            CommandContextBinding(self._command(), context)

    def test_step_mismatch_is_rejected(self):
        context = ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            run_id="run-1",
            step_id="step-2",
        )

        with self.assertRaises(ValueError):
            CommandContextBinding(self._command(), context)

    def test_binding_is_immutable(self):
        binding = bind_command_context(
            self._command(),
            self._context(),
        )

        with self.assertRaises(AttributeError):
            binding.command = self._command()


if __name__ == "__main__":
    unittest.main()
