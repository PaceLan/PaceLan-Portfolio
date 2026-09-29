import unittest

from application.commands import ExecuteTaskCommand
from application.models import (
    ApplicationExecutionModel,
    TaskModel,
)
from application.services import ApplicationExecutionService


class FakeApplicationExecutionService:
    def __init__(self):
        self.received_task = None

    def run(self, task):
        self.received_task = task
        return "application-result"


class ApplicationCommandM1873Tests(unittest.TestCase):

    def test_handler_delegates_command_task_to_application_service(self):
        from application.commands import ExecuteTaskHandler

        task = TaskModel(
            task_id="task-001",
            project_id="project-001",
        )
        command = ExecuteTaskCommand(task=task)
        service = FakeApplicationExecutionService()

        handler = ExecuteTaskHandler(service)

        result = handler.handle(command)

        self.assertEqual(result, "application-result")
        self.assertIs(service.received_task, task)

    def test_handler_rejects_invalid_command(self):
        from application.commands import ExecuteTaskHandler

        service = FakeApplicationExecutionService()
        handler = ExecuteTaskHandler(service)

        with self.assertRaises(TypeError):
            handler.handle("invalid")

    def test_handler_rejects_invalid_service(self):
        from application.commands import ExecuteTaskHandler

        with self.assertRaises(TypeError):
            ExecuteTaskHandler(object())

    def test_handler_does_not_expose_core_execution_types(self):
        from application.commands import ExecuteTaskHandler

        service = FakeApplicationExecutionService()
        handler = ExecuteTaskHandler(service)

        self.assertNotIn(
            "WorkflowTask",
            {type(value).__name__ for value in vars(handler).values()},
        )


if __name__ == "__main__":
    unittest.main()
