import unittest
from unittest.mock import MagicMock

from agent_workflow.execution_tracking import RunStatus
from agent_workflow.workflow_core import AgentWorkflow, WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_service import WorkflowService


class ResultSnapshotConsistencyTests(unittest.TestCase):

    def setUp(self) -> None:
        self.history_store = MagicMock()
        self.snapshot_service = MagicMock()

        self.workflow = AgentWorkflow(
            history_store=self.history_store,
            snapshot_service=self.snapshot_service,
        )
        self.service = WorkflowService(self.workflow)

    def test_result_and_snapshot_share_same_run_id(self):
        task = WorkflowTask(
            "task-m16-6-3",
            "Result snapshot identity test",
        )

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep(
                    "step-001",
                    lambda: "done",
                ),
            ),
        )

        result = self.service.execute(plan)

        context = self.service.last_run_context
        tracker = self.service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)

        snapshot = tracker.snapshot()

        self.assertIsInstance(result, WorkflowResult)
        self.assertEqual(
            context.run_id,
            tracker.context.run_id,
        )
        self.assertEqual(
            tracker.context.run_id,
            snapshot.run_id,
        )
        self.assertEqual(
            snapshot.run_id,
            result.run_id,
        )

    def test_result_and_snapshot_have_same_task_identity(self):
        task = WorkflowTask(
            "task-m16-6-3-task",
            "Task identity test",
        )

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep(
                    "step-001",
                    lambda: "done",
                ),
            ),
        )

        result = self.service.execute(plan)

        context = self.service.last_run_context
        tracker = self.service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)

        snapshot = tracker.snapshot()

        self.assertEqual(snapshot.task_id, context.task_id)
        self.assertEqual(context.task_id, task.task_id)
        self.assertEqual(result.run_id, context.run_id)

    def test_failed_execution_preserves_same_run_identity(self):
        task = WorkflowTask(
            "task-m16-6-3-failure",
            "Failure identity test",
        )

        def fail() -> str:
            raise RuntimeError("expected failure")

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep(
                    "step-001",
                    fail,
                ),
            ),
        )

        result = self.service.execute(plan)

        context = self.service.last_run_context
        tracker = self.service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)

        snapshot = tracker.snapshot()

        self.assertEqual(result.run_id, context.run_id)
        self.assertEqual(snapshot.run_id, context.run_id)
        self.assertEqual(snapshot.run_id, result.run_id)
        self.assertIs(snapshot.run_status, RunStatus.FAILED)


if __name__ == "__main__":
    unittest.main()
