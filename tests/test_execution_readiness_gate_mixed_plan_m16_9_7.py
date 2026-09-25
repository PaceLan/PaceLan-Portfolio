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


class ExecutionReadinessGateMixedPlanM1697Tests(unittest.TestCase):

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
            task_id="task-m1697",
            project_id="project-m1697",
            description="mixed readiness gate integration",
        )

    def _step(
        self,
        step_id,
        *,
        risk=RiskLevel.SAFE,
        approval=ApprovalStatus.NOT_REQUESTED,
        calls=None,
    ):
        def action():
            if calls is not None:
                calls.append(step_id)
            return "ok"

        return WorkflowStep(
            operation="execute",
            action=action,
            risk=risk,
            approval=approval,
            step_id=step_id,
        )

    def test_ready_then_blocked_then_remaining_steps(self):
        calls = []

        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step("step-001", calls=calls),
                self._step(
                    "step-002",
                    risk=RiskLevel.HIGH_RISK,
                    approval=ApprovalStatus.NOT_REQUESTED,
                    calls=calls,
                ),
                self._step("step-003", calls=calls),
            ),
        )

        result = self.service.execute(plan)
        tracker = self.service.last_execution_tracker

        self.assertEqual(calls, ["step-001"])

        self.assertEqual(result.total_steps, 2)
        self.assertEqual(result.successful_steps, 1)
        self.assertEqual(result.failed_steps, 0)
        self.assertEqual(result.blocked_steps, 1)
        self.assertFalse(result.completed_successfully)
        self.assertEqual(result.status, WorkflowStatus.BLOCKED)

        self.assertIsNotNone(tracker)
        assert tracker is not None
        self.assertIs(tracker.run_status, RunStatus.FAILED)

    def test_denied_step_stops_execution_after_successful_prefix(self):
        calls = []

        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step("step-001", calls=calls),
                self._step(
                    "step-002",
                    approval=ApprovalStatus.DENIED,
                    calls=calls,
                ),
                self._step("step-003", calls=calls),
            ),
        )

        result = self.service.execute(plan)

        self.assertEqual(calls, ["step-001"])
        self.assertEqual(result.successful_steps, 1)
        self.assertEqual(result.blocked_steps, 1)
        self.assertEqual(result.failed_steps, 0)
        self.assertEqual(result.status, WorkflowStatus.BLOCKED)

    def test_blocked_step_does_not_execute_following_actions(self):
        calls = []

        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step(
                    "step-001",
                    risk=RiskLevel.HIGH_RISK,
                    approval=ApprovalStatus.BLOCKED,
                    calls=calls,
                ),
                self._step("step-002", calls=calls),
                self._step("step-003", calls=calls),
            ),
        )

        result = self.service.execute(plan)

        self.assertEqual(calls, [])
        self.assertEqual(result.blocked_steps, 1)
        self.assertEqual(result.successful_steps, 0)
        self.assertEqual(result.failed_steps, 0)
        self.assertEqual(result.status, WorkflowStatus.BLOCKED)


if __name__ == "__main__":
    unittest.main()
