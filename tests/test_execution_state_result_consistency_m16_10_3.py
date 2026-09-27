import tempfile
import unittest

from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.workflow_core import AgentWorkflow, WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from agent_workflow.workflow_service import WorkflowService
from history.history_core import HistoryStore
from permissions.reporting import ApprovalStatus, RiskLevel
from snapshots.snapshot_service import SnapshotService


class TestExecutionStateResultConsistencyM16103(unittest.TestCase):

    def setUp(self):
        self._temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._temporary_directory.cleanup)

    def _service(self):
        root = self._temporary_directory.name

        history = HistoryStore(root)
        snapshots = SnapshotService(root)

        workflow = AgentWorkflow(
            history_store=history,
            snapshot_service=snapshots,
        )

        return WorkflowService(workflow)

    def _task(self, task_id):
        return WorkflowTask(
            task_id=task_id,
            description="M16.10.3 consistency",
        )

    def test_success_result_matches_tracker(self):
        task = self._task("task-success")

        plan = WorkflowPlan(
            task=task,
            steps=(
                WorkflowStep(
                    operation="one",
                    action=lambda: "one",
                    step_id="step-001",
                ),
                WorkflowStep(
                    operation="two",
                    action=lambda: "two",
                    step_id="step-002",
                ),
            ),
        )

        service = self._service()
        result = service.execute(plan)
        tracker = service.last_execution_tracker

        self.assertIsNotNone(tracker)
        self.assertEqual(tracker.run_status, RunStatus.COMPLETED)
        self.assertEqual(
            dict(tracker.step_states),
            {
                "step-001": StepStatus.SUCCESS,
                "step-002": StepStatus.SUCCESS,
            },
        )
        self.assertEqual(result.run_id, tracker.context.run_id)
        self.assertEqual(result.total_steps, 2)
        self.assertEqual(result.successful_steps, 2)
        self.assertEqual(result.failed_steps, 0)
        self.assertEqual(result.blocked_steps, 0)

    def test_success_snapshot_matches_tracker(self):
        task = self._task("task-snapshot-success")

        plan = WorkflowPlan(
            task=task,
            steps=(
                WorkflowStep(
                    operation="one",
                    action=lambda: "one",
                    step_id="step-001",
                ),
            ),
        )

        service = self._service()
        service.execute(plan)
        tracker = service.last_execution_tracker

        self.assertIsNotNone(tracker)

        snapshot = tracker.snapshot()

        self.assertEqual(snapshot.run_id, tracker.context.run_id)
        self.assertEqual(snapshot.task_id, tracker.context.task_id)
        self.assertEqual(snapshot.run_status, tracker.run_status)
        self.assertEqual(
            dict(snapshot.step_states),
            dict(tracker.step_states),
        )
        self.assertEqual(snapshot.current_step, tracker.current_step)
        self.assertEqual(snapshot.finished_at, tracker.finished_at)

    def test_snapshot_does_not_mutate_tracker(self):
        task = self._task("task-snapshot-immutable")

        plan = WorkflowPlan(
            task=task,
            steps=(
                WorkflowStep(
                    operation="one",
                    action=lambda: "one",
                    step_id="step-001",
                ),
            ),
        )

        service = self._service()
        service.execute(plan)
        tracker = service.last_execution_tracker

        self.assertIsNotNone(tracker)

        snapshot = tracker.snapshot()
        original_states = dict(tracker.step_states)

        with self.assertRaises(TypeError):
            snapshot.step_states["step-001"] = StepStatus.FAILED

        self.assertEqual(
            dict(tracker.step_states),
            original_states,
        )

    def test_failure_result_matches_tracker(self):
        task = self._task("task-failure")

        def fail():
            raise RuntimeError("intentional failure")

        plan = WorkflowPlan(
            task=task,
            steps=(
                WorkflowStep(
                    operation="one",
                    action=lambda: "one",
                    step_id="step-001",
                ),
                WorkflowStep(
                    operation="two",
                    action=fail,
                    step_id="step-002",
                ),
                WorkflowStep(
                    operation="three",
                    action=lambda: "three",
                    step_id="step-003",
                ),
            ),
        )

        service = self._service()
        result = service.execute(plan)
        tracker = service.last_execution_tracker

        self.assertIsNotNone(tracker)

        self.assertEqual(tracker.run_status, RunStatus.FAILED)
        self.assertEqual(
            dict(tracker.step_states),
            {
                "step-001": StepStatus.SUCCESS,
                "step-002": StepStatus.FAILED,
                "step-003": StepStatus.SKIPPED,
            },
        )

        self.assertEqual(result.run_id, tracker.context.run_id)
        self.assertEqual(result.total_steps, 2)
        self.assertEqual(result.successful_steps, 1)
        self.assertEqual(result.failed_steps, 1)
        self.assertEqual(result.failure_index, 1)

    def test_failure_snapshot_matches_tracker(self):
        task = self._task("task-snapshot-failure")

        def fail():
            raise RuntimeError("intentional failure")

        plan = WorkflowPlan(
            task=task,
            steps=(
                WorkflowStep(
                    operation="one",
                    action=lambda: "one",
                    step_id="step-001",
                ),
                WorkflowStep(
                    operation="two",
                    action=fail,
                    step_id="step-002",
                ),
            ),
        )

        service = self._service()
        service.execute(plan)
        tracker = service.last_execution_tracker

        self.assertIsNotNone(tracker)

        snapshot = tracker.snapshot()

        self.assertEqual(snapshot.run_status, RunStatus.FAILED)
        self.assertEqual(
            dict(snapshot.step_states),
            {
                "step-001": StepStatus.SUCCESS,
                "step-002": StepStatus.FAILED,
            },
        )
        self.assertEqual(snapshot.current_step, None)
        self.assertIsNotNone(snapshot.finished_at)

    def test_result_and_tracker_share_same_run_identity(self):
        task = self._task("task-identity")

        plan = WorkflowPlan(
            task=task,
            steps=(
                WorkflowStep(
                    operation="one",
                    action=lambda: "one",
                    step_id="step-001",
                ),
            ),
        )

        service = self._service()
        result = service.execute(plan)

        tracker = service.last_execution_tracker
        context = service.last_run_context

        self.assertIsNotNone(tracker)
        self.assertIsNotNone(context)

        self.assertEqual(result.run_id, context.run_id)
        self.assertEqual(tracker.context.run_id, context.run_id)
        self.assertEqual(tracker.context.task_id, task.task_id)

    def test_blocked_step_is_not_executed_and_matches_tracker(self):
        calls = []

        task = self._task("task-blocked")

        def blocked_action():
            calls.append("blocked")
            return "should-not-run"

        plan = WorkflowPlan(
            task=task,
            steps=(
                WorkflowStep(
                    operation="blocked-operation",
                    action=blocked_action,
                    risk=RiskLevel.HIGH_RISK,
                    approval=ApprovalStatus.NOT_REQUESTED,
                    step_id="step-001",
                ),
            ),
        )

        service = self._service()
        result = service.execute(plan)
        tracker = service.last_execution_tracker

        self.assertIsNotNone(tracker)

        self.assertEqual(calls, [])
        self.assertEqual(tracker.run_status, RunStatus.FAILED)
        self.assertEqual(
            dict(tracker.step_states),
            {
                "step-001": StepStatus.FAILED,
            },
        )

        self.assertEqual(result.run_id, tracker.context.run_id)
        self.assertEqual(result.total_steps, 1)
        self.assertEqual(result.successful_steps, 0)
        self.assertEqual(result.failed_steps, 0)
        self.assertEqual(result.blocked_steps, 1)
        self.assertEqual(result.failure_index, 0)
        self.assertFalse(result.step_results[0].success)

    def test_blocked_step_skips_following_steps(self):
        calls = []

        task = self._task("task-blocked-following")

        def first_action():
            calls.append("step-001")
            return "one"

        def blocked_action():
            calls.append("step-002")
            return "should-not-run"

        def following_action():
            calls.append("step-003")
            return "should-not-run"

        plan = WorkflowPlan(
            task=task,
            steps=(
                WorkflowStep(
                    operation="one",
                    action=first_action,
                    step_id="step-001",
                ),
                WorkflowStep(
                    operation="blocked",
                    action=blocked_action,
                    risk=RiskLevel.HIGH_RISK,
                    approval=ApprovalStatus.NOT_REQUESTED,
                    step_id="step-002",
                ),
                WorkflowStep(
                    operation="three",
                    action=following_action,
                    step_id="step-003",
                ),
            ),
        )

        service = self._service()
        result = service.execute(plan)
        tracker = service.last_execution_tracker

        self.assertIsNotNone(tracker)

        self.assertEqual(
            calls,
            ["step-001"],
        )

        self.assertEqual(tracker.run_status, RunStatus.FAILED)
        self.assertEqual(
            dict(tracker.step_states),
            {
                "step-001": StepStatus.SUCCESS,
                "step-002": StepStatus.FAILED,
                "step-003": StepStatus.SKIPPED,
            },
        )

        self.assertEqual(result.run_id, tracker.context.run_id)
        self.assertEqual(result.total_steps, 2)
        self.assertEqual(result.successful_steps, 1)
        self.assertEqual(result.failed_steps, 0)
        self.assertEqual(result.blocked_steps, 1)
        self.assertEqual(result.failure_index, 1)

    def test_blocked_execution_snapshot_matches_result_identity(self):
        task = self._task("task-blocked-snapshot")

        plan = WorkflowPlan(
            task=task,
            steps=(
                WorkflowStep(
                    operation="blocked",
                    action=lambda: "should-not-run",
                    risk=RiskLevel.HIGH_RISK,
                    approval=ApprovalStatus.NOT_REQUESTED,
                    step_id="step-001",
                ),
                WorkflowStep(
                    operation="following",
                    action=lambda: "should-not-run",
                    step_id="step-002",
                ),
            ),
        )

        service = self._service()
        result = service.execute(plan)
        tracker = service.last_execution_tracker

        self.assertIsNotNone(tracker)

        snapshot = tracker.snapshot()

        self.assertEqual(snapshot.run_id, result.run_id)
        self.assertEqual(snapshot.task_id, task.task_id)
        self.assertEqual(snapshot.run_status, RunStatus.FAILED)
        self.assertEqual(
            dict(snapshot.step_states),
            {
                "step-001": StepStatus.FAILED,
                "step-002": StepStatus.SKIPPED,
            },
        )
        self.assertIsNone(snapshot.current_step)
        self.assertIsNotNone(snapshot.finished_at)


if __name__ == "__main__":
    unittest.main()
