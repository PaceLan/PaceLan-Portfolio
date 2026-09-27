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


class ExecutionReadinessGateIntegrationM1696Tests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        history = HistoryStore(self.temp_dir.name)
        snapshots = SnapshotService(self.temp_dir.name)

        self.workflow = AgentWorkflow(
            history_store=history,
            snapshot_service=snapshots,
        )
        self.service = WorkflowService(self.workflow)

    def _task(self):
        return WorkflowTask(
            task_id="task-m1696",
            project_id="project-m1696",
            description="readiness gate integration",
        )

    def _step(
        self,
        step_id="step-001",
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

    def test_blocked_plan_does_not_execute_action(self):
        calls = []

        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step(
                    risk=RiskLevel.HIGH_RISK,
                    approval=ApprovalStatus.NOT_REQUESTED,
                    calls=calls,
                ),
            ),
        )

        result = self.service.execute(plan)
        tracker = self.service.last_execution_tracker

        self.assertEqual(calls, [])
        self.assertFalse(result.completed_successfully)
        self.assertEqual(result.total_steps, 1)
        self.assertEqual(result.successful_steps, 0)
        self.assertEqual(result.failed_steps, 0)
        self.assertEqual(result.blocked_steps, 1)
        self.assertEqual(result.status, WorkflowStatus.BLOCKED)

        self.assertIsNotNone(tracker)
        assert tracker is not None
        self.assertIs(tracker.run_status, RunStatus.FAILED)

    def test_denied_plan_does_not_execute_action(self):
        calls = []

        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step(
                    approval=ApprovalStatus.DENIED,
                    calls=calls,
                ),
            ),
        )

        result = self.service.execute(plan)
        tracker = self.service.last_execution_tracker

        self.assertEqual(calls, [])
        self.assertFalse(result.completed_successfully)
        self.assertEqual(result.total_steps, 1)
        self.assertEqual(result.successful_steps, 0)
        self.assertEqual(result.failed_steps, 0)
        self.assertEqual(result.blocked_steps, 1)
        self.assertEqual(result.status, WorkflowStatus.BLOCKED)

        self.assertIsNotNone(tracker)
        assert tracker is not None
        self.assertIs(tracker.run_status, RunStatus.FAILED)

    def test_ready_plan_executes_normally(self):
        calls = []

        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step(calls=calls),
            ),
        )

        result = self.service.execute(plan)

        self.assertEqual(calls, ["step-001"])
        self.assertEqual(len(result.step_results), 1)
        self.assertTrue(result.step_results[0].success)

    def test_blocked_plan_does_not_mutate_original_plan(self):
        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step(
                    risk=RiskLevel.HIGH_RISK,
                    approval=ApprovalStatus.BLOCKED,
                ),
            ),
        )

        original_task = plan.task
        original_steps = plan.steps
        original_step = plan.steps[0]

        result = self.service.execute(plan)

        self.assertFalse(result.completed_successfully)
        self.assertIs(plan.task, original_task)
        self.assertIs(plan.steps, original_steps)
        self.assertIs(plan.steps[0], original_step)

    def test_blocked_plan_is_deterministically_rejected(self):
        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step(
                    risk=RiskLevel.HIGH_RISK,
                    approval=ApprovalStatus.NOT_REQUESTED,
                ),
            ),
        )

        first = self.service.execute(plan)

        second = self.service.execute(plan)

        first_signature = (
            first.status,
            first.total_steps,
            first.successful_steps,
            first.failed_steps,
            first.blocked_steps,
            first.completed_successfully,
            tuple(
                (
                    item.operation,
                    item.status,
                    item.success,
                )
                for item in first.step_results
            ),
        )

        second_signature = (
            second.status,
            second.total_steps,
            second.successful_steps,
            second.failed_steps,
            second.blocked_steps,
            second.completed_successfully,
            tuple(
                (
                    item.operation,
                    item.status,
                    item.success,
                )
                for item in second.step_results
            ),
        )

        self.assertEqual(first_signature, second_signature)

    def test_blocked_plan_preserves_task_and_step_identity(self):
        task = self._task()
        step = self._step(
            risk=RiskLevel.HIGH_RISK,
            approval=ApprovalStatus.DENIED,
        )

        plan = WorkflowPlan(
            task=task,
            steps=(step,),
        )

        result = self.service.execute(plan)

        self.assertFalse(result.completed_successfully)
        self.assertIs(plan.task, task)
        self.assertIs(plan.steps[0], step)
        self.assertEqual(result.run_id, self.service.last_run_context.run_id)


if __name__ == "__main__":
    unittest.main()
