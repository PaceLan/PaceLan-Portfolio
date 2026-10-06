import unittest

from application.execution_context import ExecutionContext
from application.task_context import TaskContext
from application.task_context_binding import (
    TaskContextBinding,
    bind_task_context,
)


class TestTaskContextBinding(unittest.TestCase):

    def _task(self):
        return TaskContext(
            project_id="project-1",
            task_id="task-1",
            workflow_id="workflow-1",
        )

    def _context(self):
        return ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            workflow_id="workflow-1",
            run_id="run-1",
            step_id="step-1",
        )

    def test_binding_preserves_task_and_context(self):
        task = self._task()
        context = self._context()

        binding = bind_task_context(task, context)

        self.assertIs(binding.task, task)
        self.assertIs(binding.context, context)

    def test_binding_exposes_task_identity(self):
        binding = bind_task_context(
            self._task(),
            self._context(),
        )

        self.assertEqual(binding.project_id, "project-1")
        self.assertEqual(binding.task_id, "task-1")
        self.assertEqual(binding.workflow_id, "workflow-1")
        self.assertEqual(binding.run_id, "run-1")

    def test_project_mismatch_is_rejected(self):
        context = ExecutionContext(
            project_id="project-2",
            task_id="task-1",
            workflow_id="workflow-1",
            run_id="run-1",
            step_id="step-1",
        )

        with self.assertRaises(ValueError):
            TaskContextBinding(self._task(), context)

    def test_task_mismatch_is_rejected(self):
        context = ExecutionContext(
            project_id="project-1",
            task_id="task-2",
            workflow_id="workflow-1",
            run_id="run-1",
            step_id="step-1",
        )

        with self.assertRaises(ValueError):
            TaskContextBinding(self._task(), context)

    def test_workflow_mismatch_is_rejected(self):
        context = ExecutionContext(
            project_id="project-1",
            task_id="task-1",
            workflow_id="workflow-2",
            run_id="run-1",
            step_id="step-1",
        )

        with self.assertRaises(ValueError):
            TaskContextBinding(self._task(), context)

    def test_binding_is_immutable(self):
        binding = bind_task_context(
            self._task(),
            self._context(),
        )

        with self.assertRaises(AttributeError):
            binding.task = self._task()


if __name__ == "__main__":
    unittest.main()
