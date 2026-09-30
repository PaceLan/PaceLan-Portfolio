import unittest

from agent_workflow.workflow_core import (
    AgentWorkflow,
    WorkflowTask,
)
from agent_workflow.workflow_plan import (
    WorkflowPlan,
    WorkflowStep,
)
from agent_workflow.workflow_service import WorkflowService
from unittest.mock import MagicMock


class SummaryMetadataConsistencyTests(unittest.TestCase):

    def setUp(self) -> None:
        self.workflow = AgentWorkflow(
            history_store=MagicMock(),
            snapshot_service=MagicMock(),
        )
        self.service = WorkflowService(self.workflow)

    def test_success_summary_matches_result_metadata(self):
        task = WorkflowTask(
            "task-m16-6-4-success",
            "Summary metadata success test",
        )

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step-001", lambda: "one"),
                WorkflowStep("step-002", lambda: "two"),
            ),
        )

        result = self.service.execute(plan)
        summary = result.summary()

        self.assertIn(
            f"Total steps: {result.total_steps}",
            summary,
        )
        self.assertIn(
            f"Successful steps: {result.successful_steps}",
            summary,
        )
        self.assertIn(
            f"Failed steps: {result.failed_steps}",
            summary,
        )
        self.assertIn(
            f"Blocked steps: {result.blocked_steps}",
            summary,
        )
        self.assertIn(
            f"Completed successfully: {result.completed_successfully}",
            summary,
        )
        self.assertIn("Failure step: None", summary)

    def test_failure_summary_matches_result_metadata(self):
        task = WorkflowTask(
            "task-m16-6-4-failure",
            "Summary metadata failure test",
        )

        def fail() -> str:
            raise RuntimeError("expected failure")

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step-001", lambda: "one"),
                WorkflowStep("step-002", fail),
                WorkflowStep("step-003", lambda: "three"),
            ),
        )

        result = self.service.execute(plan)
        summary = result.summary()

        self.assertIn(
            f"Total steps: {result.total_steps}",
            summary,
        )
        self.assertIn(
            f"Successful steps: {result.successful_steps}",
            summary,
        )
        self.assertIn(
            f"Failed steps: {result.failed_steps}",
            summary,
        )
        self.assertIn(
            f"Blocked steps: {result.blocked_steps}",
            summary,
        )
        self.assertIn(
            f"Completed successfully: {result.completed_successfully}",
            summary,
        )

        self.assertIsNotNone(result.failure_index)
        self.assertIn(
            f"Failure step: {result.failure_index + 1}",
            summary,
        )

    def test_summary_is_deterministic(self):
        task = WorkflowTask(
            "task-m16-6-4-deterministic",
            "Summary deterministic test",
        )

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step-001", lambda: "done"),
            ),
        )

        result = self.service.execute(plan)

        self.assertEqual(
            result.summary(),
            result.summary(),
        )


if __name__ == "__main__":
    unittest.main()
