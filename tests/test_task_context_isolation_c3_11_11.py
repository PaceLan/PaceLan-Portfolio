import unittest

from application.universal_agent_interface import UniversalAgentInterface
from tests.test_universal_agent_interface import _FakeBackend


class TaskContextIsolationTests(unittest.TestCase):
    def test_context_is_immutable(self):
        interface = UniversalAgentInterface(_FakeBackend())
        task = interface.create_task("project-1", "inspect", task_id="task-1")
        context = interface.task_context(task.task.task_id)

        with self.assertRaises(AttributeError):
            context.task_id = "task-2"

    def test_context_identity_survives_task_state_changes(self):
        interface = UniversalAgentInterface(_FakeBackend())
        task = interface.create_task("project-1", "inspect", task_id="task-1")
        context_before = interface.task_context("task-1")

        interface.submit_task("task-1", ())

        context_after = interface.task_context("task-1")

        self.assertEqual(context_before, context_after)
        self.assertEqual(context_after.project_id, "project-1")
        self.assertEqual(context_after.task_id, "task-1")
        self.assertIsNone(context_after.workflow_id)


if __name__ == "__main__":
    unittest.main()
