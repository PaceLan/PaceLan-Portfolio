import unittest

from application.universal_agent_interface import UniversalAgentInterface
from tests.test_universal_agent_interface import _FakeBackend


class TaskContextInterfaceTests(unittest.TestCase):
    def setUp(self):
        self.interface = UniversalAgentInterface(_FakeBackend())

    def test_task_context_maps_task_identity(self):
        task = self.interface.create_task(
            "project-1",
            "inspect",
            task_id="task-1",
        )

        context = self.interface.task_context(task.task.task_id)

        self.assertEqual(context.project_id, "project-1")
        self.assertEqual(context.task_id, "task-1")
        self.assertIsNone(context.workflow_id)

    def test_task_context_accepts_workflow_id(self):
        task = self.interface.create_task(
            "project-1",
            "inspect",
            task_id="task-2",
        )

        context = self.interface.task_context(
            task.task.task_id,
            workflow_id="workflow-1",
        )

        self.assertEqual(context.workflow_id, "workflow-1")

    def test_task_context_does_not_change_task(self):
        task = self.interface.create_task(
            "project-1",
            "inspect",
            context="original",
            task_id="task-3",
        )

        self.interface.task_context(task.task.task_id)

        current = self.interface.inspect_task(task.task.task_id)
        self.assertEqual(current.task.project_id, "project-1")
        self.assertEqual(current.task.task_id, "task-3")
        self.assertEqual(current.task.context, "original")


if __name__ == "__main__":
    unittest.main()
