import unittest
from dataclasses import FrozenInstanceError

from application.commands import ExecuteTaskCommand
from application.models import TaskModel


class ApplicationCommandM1871Tests(unittest.TestCase):

    def test_command_is_frozen(self):
        command = ExecuteTaskCommand(
            task=TaskModel(
                task_id="task-001",
                project_id="project-001",
            )
        )

        with self.assertRaises(FrozenInstanceError):
            command.task = TaskModel(
                task_id="changed",
                project_id="project-001",
            )

    def test_command_contains_application_task(self):
        task = TaskModel(
            task_id="task-002",
            project_id="project-002",
        )

        command = ExecuteTaskCommand(task=task)

        self.assertIs(command.task, task)

    def test_command_rejects_non_application_task(self):
        with self.assertRaises(TypeError):
            ExecuteTaskCommand(task="invalid")

    def test_command_does_not_expose_core_execution_objects(self):
        command = ExecuteTaskCommand(
            task=TaskModel(
                task_id="task-003",
                project_id="project-003",
            )
        )

        self.assertEqual(
            type(command.task).__name__,
            "TaskModel",
        )

        self.assertNotIn(
            "WorkflowTask",
            {
                type(value).__name__
                for value in vars(command).values()
            },
        )


if __name__ == "__main__":
    unittest.main()
