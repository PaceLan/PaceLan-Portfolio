import unittest

from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_run import WorkflowRunContext


class WorkflowRunContextTests(unittest.TestCase):
    def test_direct_construction(self):
        context = WorkflowRunContext(
            run_id="run-001",
            task_id="task-001",
        )

        self.assertEqual(context.run_id, "run-001")
        self.assertEqual(context.task_id, "task-001")

    def test_create_uses_task_identity(self):
        task = WorkflowTask(
            task_id="task-001",
            description="Test task",
            context={},
        )

        context = WorkflowRunContext.create(task)

        self.assertEqual(context.task_id, "task-001")
        self.assertIsInstance(context.run_id, str)
        self.assertTrue(context.run_id)

    def test_create_generates_unique_run_ids(self):
        task = WorkflowTask(
            task_id="task-001",
            description="Test task",
            context={},
        )

        first = WorkflowRunContext.create(task)
        second = WorkflowRunContext.create(task)

        self.assertNotEqual(first.run_id, second.run_id)
        self.assertEqual(first.task_id, second.task_id)

    def test_same_task_can_have_multiple_runs(self):
        task = WorkflowTask(
            task_id="task-001",
            description="Test task",
            context={},
        )

        runs = [WorkflowRunContext.create(task) for _ in range(3)]

        self.assertEqual(
            {run.task_id for run in runs},
            {"task-001"},
        )
        self.assertEqual(
            len({run.run_id for run in runs}),
            3,
        )

    def test_empty_run_id_rejected(self):
        with self.assertRaises(ValueError):
            WorkflowRunContext(run_id="", task_id="task-001")

    def test_empty_task_id_rejected(self):
        with self.assertRaises(ValueError):
            WorkflowRunContext(run_id="run-001", task_id="")

    def test_non_string_run_id_rejected(self):
        with self.assertRaises(ValueError):
            WorkflowRunContext(run_id=123, task_id="task-001")

    def test_non_string_task_id_rejected(self):
        with self.assertRaises(ValueError):
            WorkflowRunContext(run_id="run-001", task_id=123)

    def test_create_requires_workflow_task(self):
        with self.assertRaises(TypeError):
            WorkflowRunContext.create("not-a-task")

    def test_run_id_is_immutable(self):
        context = WorkflowRunContext(
            run_id="run-001",
            task_id="task-001",
        )

        with self.assertRaises((AttributeError, TypeError)):
            context.run_id = "run-002"

    def test_task_id_is_immutable(self):
        context = WorkflowRunContext(
            run_id="run-001",
            task_id="task-001",
        )

        with self.assertRaises((AttributeError, TypeError)):
            context.task_id = "task-002"

    def test_context_contains_only_identity_fields(self):
        context = WorkflowRunContext(
            run_id="run-001",
            task_id="task-001",
        )

        self.assertEqual(
            set(context.__dataclass_fields__),
            {"run_id", "task_id"},
        )


if __name__ == "__main__":
    unittest.main()
