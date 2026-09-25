import tempfile
import unittest

from agent_workflow.workflow_core import (
    AgentWorkflow,
    WorkflowStatus,
    WorkflowTask,
)
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from agent_workflow.workflow_service import WorkflowService
from agent_workflow.execution_tracking import RunStatus
from history.history_core import HistoryStore
from snapshots.snapshot_service import SnapshotService
from permissions.reporting import ApprovalStatus, RiskLevel


class ExecutionReadinessTrackerConsistencyM1697Tests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.workflow = AgentWorkflow(
            history_store=HistoryStore(self.temp_dir.name),
            snapshot_service=SnapshotService(self.temp_dir.name),
        )
        self.service = WorkflowService(self.workflow)

    def _task(self):
        return WorkflowTask(
            task_id="task-m1697-tracker",
            project_id="project-m1697",
            description="tracker consistency",
        )

    def _step(
        self,
        step_id,
        *,
        risk=RiskLevel.SAFE,
        approval=ApprovalStatus.NOT_REQUESTED,
    ):
        return WorkflowStep(
            operation="execute",
            action=lambda: "ok",
            risk=risk,
            approval=approval,
            step_id=step_id,
        )

    def test_blocked_result_matches_failed_tracker(self):
        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step(
                    "step-001",
                    risk=RiskLevel.HIGH_RISK,
                    approval=ApprovalStatus.NOT_REQUESTED,
                ),
            ),
        )

        result = self.service.execute(plan)
        tracker = self.service.last_execution_tracker

        self.assertEqual(result.status, WorkflowStatus.BLOCKED)
        self.assertIsNotNone(tracker)
        assert tracker is not None
        self.assertIs(tracker.run_status, RunStatus.FAILED)

    def test_successful_result_matches_completed_tracker(self):
        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step("step-001"),
            ),
        )

        result = self.service.execute(plan)
        tracker = self.service.last_execution_tracker

        self.assertTrue(result.completed_successfully)
        self.assertEqual(result.status, WorkflowStatus.COMPLETED)
        self.assertIsNotNone(tracker)
        assert tracker is not None
        self.assertIs(tracker.run_status, RunStatus.COMPLETED)

    def test_blocked_step_is_not_reported_as_failed_step(self):
        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step(
                    "step-001",
                    approval=ApprovalStatus.DENIED,
                ),
            ),
        )

        result = self.service.execute(plan)

        self.assertEqual(result.blocked_steps, 1)
        self.assertEqual(result.failed_steps, 0)

    def test_run_id_is_shared_by_result_and_context(self):
        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step("step-001"),
            ),
        )

        result = self.service.execute(plan)

        self.assertIsNotNone(self.service.last_run_context)
        assert self.service.last_run_context is not None

        self.assertEqual(
            result.run_id,
            self.service.last_run_context.run_id,
        )


if __name__ == "__main__":
    unittest.main()
