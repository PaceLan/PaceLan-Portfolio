import unittest

from application.external_agent import ExternalAgentRequest


class ExternalAgentTaskContextTests(unittest.TestCase):
    def test_request_maps_to_task_context(self):
        request = ExternalAgentRequest(
            task_id="task-1",
            payload="inspect",
            workflow_id="workflow-1",
        )

        context = request.to_task_context("project-1")

        self.assertEqual(context.project_id, "project-1")
        self.assertEqual(context.task_id, "task-1")
        self.assertEqual(context.workflow_id, "workflow-1")

    def test_workflow_id_remains_optional(self):
        request = ExternalAgentRequest(
            task_id="task-2",
            payload="inspect",
        )

        context = request.to_task_context("project-1")

        self.assertIsNone(context.workflow_id)

    def test_empty_project_is_rejected(self):
        request = ExternalAgentRequest(
            task_id="task-3",
            payload="inspect",
        )

        with self.assertRaises(ValueError):
            request.to_task_context(" ")

if __name__ == "__main__":
    unittest.main()
