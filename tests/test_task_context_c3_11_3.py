import unittest

from application.task_context import TaskContext


class TaskContextTests(unittest.TestCase):
    def test_creates_context(self):
        context = TaskContext(
            project_id="project-1",
            task_id="task-1",
            workflow_id="workflow-1",
        )

        self.assertEqual(context.project_id, "project-1")
        self.assertEqual(context.task_id, "task-1")
        self.assertEqual(context.workflow_id, "workflow-1")

    def test_workflow_id_is_optional(self):
        context = TaskContext(
            project_id="project-1",
            task_id="task-1",
        )

        self.assertIsNone(context.workflow_id)

    def test_empty_project_rejected(self):
        with self.assertRaises(ValueError):
            TaskContext(project_id=" ", task_id="task-1")

    def test_empty_task_rejected(self):
        with self.assertRaises(ValueError):
            TaskContext(project_id="project-1", task_id=" ")

    def test_empty_workflow_rejected(self):
        with self.assertRaises(ValueError):
            TaskContext(
                project_id="project-1",
                task_id="task-1",
                workflow_id=" ",
            )

    def test_context_is_read_only(self):
        context = TaskContext("project-1", "task-1")

        with self.assertRaises(AttributeError):
            context.task_id = "task-2"


if __name__ == "__main__":
    unittest.main()
