import unittest

from application.external_agent import ExternalAgentRequest
from application.task_context import TaskContext
from application.universal_agent_interface import UniversalAgentInterface
from tests.test_universal_agent_interface import _FakeBackend


class UnifiedTaskContextConsistencyTests(unittest.TestCase):
    def test_universal_agent_and_external_request_share_identity(self):
        interface = UniversalAgentInterface(_FakeBackend())
        task = interface.create_task(
            "project-1",
            "inspect",
            task_id="task-1",
        )

        local = interface.task_context(
            task.task.task_id,
            workflow_id="workflow-1",
        )

        external = ExternalAgentRequest(
            task_id="task-1",
            payload="inspect",
            workflow_id="workflow-1",
        ).to_task_context("project-1")

        self.assertEqual(local, external)

    def test_context_has_only_identity_fields(self):
        fields = set(TaskContext.__dataclass_fields__)
        self.assertEqual(
            fields,
            {"project_id", "task_id", "workflow_id"},
        )


if __name__ == "__main__":
    unittest.main()
