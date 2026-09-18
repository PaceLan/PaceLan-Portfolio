import tempfile
import unittest
from pathlib import Path

from agent_workflow.execution_summary import ExecutionSummary
from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.result_analysis import WorkflowResultAnalysis
from agent_workflow.workflow_core import (
    AgentWorkflow,
    WorkflowStatus,
    WorkflowTask,
)
from agent_workflow.workflow_plan import WorkflowStep
from agent_workflow.workflow_service import WorkflowService
from history.history_core import HistoryStore
from permissions.reporting import ApprovalStatus
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class WorkflowIntegrationTests(unittest.TestCase):

    def make_service(self) -> WorkflowService:
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)

        root = Path(temporary_directory.name)
        project_root = root / "project"
        snapshot_root = root / "snapshots"
        history_root = root / "history"

        project_root.mkdir()
        history_root.mkdir()

        (project_root / "main.py").write_text(
            "print('baseline')\n",
            encoding="utf-8",
        )

        snapshot_store = SnapshotStore(
            project_root,
            snapshot_root,
        )

        workflow = AgentWorkflow(
            history_store=HistoryStore(history_root),
            snapshot_service=SnapshotService(
                project_root,
                store=snapshot_store,
            ),
        )

        return WorkflowService(workflow)

    def test_full_success_chain(self) -> None:
        service = self.make_service()

        task = WorkflowTask(
            task_id="integration-success",
            description="Run successful workflow",
        )

        plan = service.build(
            task,
            (
                WorkflowStep(
                    operation="step-one",
                    action=lambda: "one",
                ),
                WorkflowStep(
                    operation="step-two",
                    action=lambda: "two",
                ),
            ),
        )

        result = service.execute(plan)

        context = service.last_run_context
        tracker = service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)

        assert context is not None
        assert tracker is not None

        snapshot = tracker.snapshot()
        analysis = WorkflowResultAnalysis.from_result(result)
        summary = ExecutionSummary.from_result_and_snapshot(
            result,
            snapshot,
        )

        self.assertEqual(context.task_id, task.task_id)
        self.assertEqual(context.run_id, snapshot.run_id)

        self.assertEqual(result.status, WorkflowStatus.COMPLETED)
        self.assertTrue(result.completed_successfully)
        self.assertEqual(result.total_steps, 2)
        self.assertEqual(result.successful_steps, 2)
        self.assertEqual(result.failed_steps, 0)
        self.assertEqual(result.blocked_steps, 0)
        self.assertIsNone(result.failure_index)

        self.assertEqual(tracker.run_status, RunStatus.COMPLETED)
        self.assertIsNone(tracker.current_step)

        self.assertEqual(
            snapshot.step_states,
            {
                "step-one": StepStatus.SUCCESS,
                "step-two": StepStatus.SUCCESS,
            },
        )

        self.assertTrue(analysis.is_successful)
        self.assertFalse(analysis.has_failure)
        self.assertFalse(analysis.has_blocked_step)
        self.assertIsNone(analysis.first_failed_step)
        self.assertEqual(analysis.failed_operations, ())
        self.assertEqual(analysis.blocked_operations, ())
        self.assertEqual(
            analysis.successful_operations,
            ("step-one", "step-two"),
        )

        self.assertEqual(summary.planned_steps, 2)
        self.assertEqual(summary.executed_steps, 2)
        self.assertEqual(summary.successful_steps, 2)
        self.assertEqual(summary.failed_steps, 0)
        self.assertEqual(summary.blocked_steps, 0)
        self.assertEqual(summary.skipped_steps, 0)
        self.assertIsNone(summary.first_failure)

    def test_failure_chain_preserves_result_tracker_and_summary(
        self,
    ) -> None:
        service = self.make_service()

        third_executed = False

        def failing_action() -> str:
            raise RuntimeError("intentional failure")

        def third_action() -> str:
            nonlocal third_executed
            third_executed = True
            return "third"

        task = WorkflowTask(
            task_id="integration-failure",
            description="Run failing workflow",
        )

        plan = service.build(
            task,
            (
                WorkflowStep(
                    operation="first",
                    action=lambda: "first",
                ),
                WorkflowStep(
                    operation="second",
                    action=failing_action,
                ),
                WorkflowStep(
                    operation="third",
                    action=third_action,
                ),
            ),
        )

        result = service.execute(plan)

        context = service.last_run_context
        tracker = service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)

        assert context is not None
        assert tracker is not None

        snapshot = tracker.snapshot()
        analysis = WorkflowResultAnalysis.from_result(result)
        summary = ExecutionSummary.from_result_and_snapshot(
            result,
            snapshot,
        )

        self.assertFalse(third_executed)

        self.assertEqual(context.task_id, task.task_id)
        self.assertEqual(context.run_id, snapshot.run_id)

        self.assertEqual(result.status, WorkflowStatus.FAILED)
        self.assertFalse(result.completed_successfully)
        self.assertEqual(result.total_steps, 2)
        self.assertEqual(result.successful_steps, 1)
        self.assertEqual(result.failed_steps, 1)
        self.assertEqual(result.blocked_steps, 0)
        self.assertEqual(result.failure_index, 1)

        self.assertEqual(tracker.run_status, RunStatus.FAILED)
        self.assertIsNone(tracker.current_step)

        self.assertEqual(
            snapshot.step_states,
            {
                "first": StepStatus.SUCCESS,
                "second": StepStatus.FAILED,
                "third": StepStatus.SKIPPED,
            },
        )

        self.assertFalse(analysis.is_successful)
        self.assertTrue(analysis.has_failure)
        self.assertFalse(analysis.has_blocked_step)

        self.assertIsNotNone(analysis.first_failed_step)
        assert analysis.first_failed_step is not None
        self.assertEqual(
            analysis.first_failed_step.operation,
            "second",
        )

        self.assertEqual(
            analysis.failed_operations,
            ("second",),
        )
        self.assertEqual(analysis.blocked_operations, ())
        self.assertEqual(
            analysis.successful_operations,
            ("first",),
        )

        self.assertEqual(summary.planned_steps, 3)
        self.assertEqual(summary.executed_steps, 2)
        self.assertEqual(summary.successful_steps, 1)
        self.assertEqual(summary.failed_steps, 1)
        self.assertEqual(summary.blocked_steps, 0)
        self.assertEqual(summary.skipped_steps, 1)
        self.assertEqual(summary.first_failure, 1)

    def test_blocked_chain_preserves_result_tracker_and_summary(
        self,
    ) -> None:
        service = self.make_service()

        blocked_executed = False
        third_executed = False

        def blocked_action() -> str:
            nonlocal blocked_executed
            blocked_executed = True
            return "must not execute"

        def third_action() -> str:
            nonlocal third_executed
            third_executed = True
            return "must not execute"

        task = WorkflowTask(
            task_id="integration-blocked",
            description="Run blocked workflow",
        )

        plan = service.build(
            task,
            (
                WorkflowStep(
                    operation="first",
                    action=lambda: "first",
                ),
                WorkflowStep(
                    operation="blocked",
                    action=blocked_action,
                    approval=ApprovalStatus.BLOCKED,
                ),
                WorkflowStep(
                    operation="third",
                    action=third_action,
                ),
            ),
        )

        result = service.execute(plan)

        context = service.last_run_context
        tracker = service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)

        assert context is not None
        assert tracker is not None

        snapshot = tracker.snapshot()
        analysis = WorkflowResultAnalysis.from_result(result)
        summary = ExecutionSummary.from_result_and_snapshot(
            result,
            snapshot,
        )

        self.assertFalse(blocked_executed)
        self.assertFalse(third_executed)

        self.assertEqual(context.task_id, task.task_id)
        self.assertEqual(context.run_id, snapshot.run_id)

        self.assertEqual(result.status, WorkflowStatus.BLOCKED)
        self.assertFalse(result.completed_successfully)
        self.assertEqual(result.total_steps, 2)
        self.assertEqual(result.successful_steps, 1)
        self.assertEqual(result.failed_steps, 0)
        self.assertEqual(result.blocked_steps, 1)
        self.assertEqual(result.failure_index, 1)

        self.assertEqual(tracker.run_status, RunStatus.FAILED)
        self.assertIsNone(tracker.current_step)

        self.assertEqual(
            snapshot.step_states,
            {
                "first": StepStatus.SUCCESS,
                "blocked": StepStatus.FAILED,
                "third": StepStatus.SKIPPED,
            },
        )

        self.assertFalse(analysis.is_successful)
        self.assertFalse(analysis.has_failure)
        self.assertTrue(analysis.has_blocked_step)
        self.assertIsNone(analysis.first_failed_step)
        self.assertEqual(analysis.failed_operations, ())
        self.assertEqual(
            analysis.blocked_operations,
            ("blocked",),
        )
        self.assertEqual(
            analysis.successful_operations,
            ("first",),
        )

        self.assertEqual(summary.planned_steps, 3)
        self.assertEqual(summary.executed_steps, 2)
        self.assertEqual(summary.successful_steps, 1)
        self.assertEqual(summary.failed_steps, 0)
        self.assertEqual(summary.blocked_steps, 1)
        self.assertEqual(summary.skipped_steps, 1)
        self.assertEqual(summary.first_failure, 1)

    def test_empty_plan_preserves_result_tracker_and_summary(
        self,
    ) -> None:
        service = self.make_service()

        task = WorkflowTask(
            task_id="integration-empty",
            description="Run empty workflow",
        )

        plan = service.build(
            task,
            (),
        )

        result = service.execute(plan)

        context = service.last_run_context
        tracker = service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)

        assert context is not None
        assert tracker is not None

        snapshot = tracker.snapshot()
        analysis = WorkflowResultAnalysis.from_result(result)
        summary = ExecutionSummary.from_result_and_snapshot(
            result,
            snapshot,
        )

        self.assertEqual(context.task_id, task.task_id)
        self.assertEqual(context.run_id, snapshot.run_id)

        self.assertEqual(result.total_steps, 0)
        self.assertEqual(result.successful_steps, 0)
        self.assertEqual(result.failed_steps, 0)
        self.assertEqual(result.blocked_steps, 0)
        self.assertIsNone(result.failure_index)

        self.assertIsNone(tracker.current_step)

        self.assertEqual(snapshot.step_states, {})

        self.assertFalse(analysis.has_failure)
        self.assertFalse(analysis.has_blocked_step)
        self.assertIsNone(analysis.first_failed_step)
        self.assertEqual(analysis.failed_operations, ())
        self.assertEqual(analysis.blocked_operations, ())
        self.assertEqual(analysis.successful_operations, ())

        self.assertEqual(summary.planned_steps, 0)
        self.assertEqual(summary.executed_steps, 0)
        self.assertEqual(summary.successful_steps, 0)
        self.assertEqual(summary.failed_steps, 0)
        self.assertEqual(summary.blocked_steps, 0)
        self.assertEqual(summary.skipped_steps, 0)
        self.assertIsNone(summary.first_failure)

    def test_single_step_failure_preserves_result_tracker_and_summary(
        self,
    ) -> None:
        service = self.make_service()

        def failing_action() -> str:
            raise RuntimeError("intentional single-step failure")

        task = WorkflowTask(
            task_id="integration-single-failure",
            description="Run single-step failing workflow",
        )

        plan = service.build(
            task,
            (
                WorkflowStep(
                    operation="only-step",
                    action=failing_action,
                ),
            ),
        )

        result = service.execute(plan)

        context = service.last_run_context
        tracker = service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)

        assert context is not None
        assert tracker is not None

        snapshot = tracker.snapshot()
        analysis = WorkflowResultAnalysis.from_result(result)
        summary = ExecutionSummary.from_result_and_snapshot(
            result,
            snapshot,
        )

        self.assertEqual(context.task_id, task.task_id)
        self.assertEqual(context.run_id, snapshot.run_id)

        self.assertEqual(result.status, WorkflowStatus.FAILED)
        self.assertFalse(result.completed_successfully)
        self.assertEqual(result.total_steps, 1)
        self.assertEqual(result.successful_steps, 0)
        self.assertEqual(result.failed_steps, 1)
        self.assertEqual(result.blocked_steps, 0)
        self.assertEqual(result.failure_index, 0)

        self.assertEqual(tracker.run_status, RunStatus.FAILED)
        self.assertIsNone(tracker.current_step)

        self.assertEqual(
            snapshot.step_states,
            {
                "only-step": StepStatus.FAILED,
            },
        )

        self.assertFalse(analysis.is_successful)
        self.assertTrue(analysis.has_failure)
        self.assertFalse(analysis.has_blocked_step)

        self.assertIsNotNone(analysis.first_failed_step)
        assert analysis.first_failed_step is not None
        self.assertEqual(
            analysis.first_failed_step.operation,
            "only-step",
        )

        self.assertEqual(
            analysis.failed_operations,
            ("only-step",),
        )
        self.assertEqual(analysis.blocked_operations, ())
        self.assertEqual(analysis.successful_operations, ())

        self.assertEqual(summary.planned_steps, 1)
        self.assertEqual(summary.executed_steps, 1)
        self.assertEqual(summary.successful_steps, 0)
        self.assertEqual(summary.failed_steps, 1)
        self.assertEqual(summary.blocked_steps, 0)
        self.assertEqual(summary.skipped_steps, 0)
        self.assertEqual(summary.first_failure, 0)

    def test_single_step_blocked_preserves_result_tracker_and_summary(
        self,
    ) -> None:
        service = self.make_service()

        blocked_executed = False

        def blocked_action() -> str:
            nonlocal blocked_executed
            blocked_executed = True
            return "must not execute"

        task = WorkflowTask(
            task_id="integration-single-blocked",
            description="Run single-step blocked workflow",
        )

        plan = service.build(
            task,
            (
                WorkflowStep(
                    operation="only-step",
                    action=blocked_action,
                    approval=ApprovalStatus.BLOCKED,
                ),
            ),
        )

        result = service.execute(plan)

        context = service.last_run_context
        tracker = service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)

        assert context is not None
        assert tracker is not None

        snapshot = tracker.snapshot()
        analysis = WorkflowResultAnalysis.from_result(result)
        summary = ExecutionSummary.from_result_and_snapshot(
            result,
            snapshot,
        )

        # Blocked action must never execute.
        self.assertFalse(blocked_executed)

        self.assertEqual(context.task_id, task.task_id)
        self.assertEqual(context.run_id, snapshot.run_id)

        # Result layer
        self.assertEqual(result.status, WorkflowStatus.BLOCKED)
        self.assertFalse(result.completed_successfully)
        self.assertEqual(result.total_steps, 1)
        self.assertEqual(result.successful_steps, 0)
        self.assertEqual(result.failed_steps, 0)
        self.assertEqual(result.blocked_steps, 1)
        self.assertEqual(result.failure_index, 0)

        # Tracker layer
        self.assertEqual(tracker.run_status, RunStatus.FAILED)
        self.assertIsNone(tracker.current_step)

        # Snapshot layer
        self.assertEqual(
            snapshot.step_states,
            {
                "only-step": StepStatus.FAILED,
            },
        )

        # Analysis layer
        self.assertFalse(analysis.is_successful)
        self.assertFalse(analysis.has_failure)
        self.assertTrue(analysis.has_blocked_step)

        self.assertIsNone(analysis.first_failed_step)

        self.assertEqual(
            analysis.failed_operations,
            (),
        )
        self.assertEqual(
            analysis.blocked_operations,
            ("only-step",),
        )
        self.assertEqual(
            analysis.successful_operations,
            (),
        )

        # Summary layer
        self.assertEqual(summary.planned_steps, 1)
        self.assertEqual(summary.executed_steps, 1)
        self.assertEqual(summary.successful_steps, 0)
        self.assertEqual(summary.failed_steps, 0)
        self.assertEqual(summary.blocked_steps, 1)
        self.assertEqual(summary.skipped_steps, 0)
        self.assertEqual(summary.first_failure, 0)
if __name__ == "__main__":
    unittest.main()