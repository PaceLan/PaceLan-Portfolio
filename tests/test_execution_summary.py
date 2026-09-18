import unittest

from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_summary import ExecutionSummary
from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.workflow_core import WorkflowStatus, WorkflowStepResult
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_run import WorkflowRunContext


class ExecutionSummaryTests(unittest.TestCase):

    def step_result(
        self,
        operation: str,
        status: WorkflowStatus,
        result: str,
        success: bool,
    ) -> WorkflowStepResult:
        return WorkflowStepResult(
            operation=operation,
            status=status,
            result=result,
            success=success,
        )

    def result(
        self,
        *step_results: WorkflowStepResult,
    ) -> WorkflowResult:
        return WorkflowResult.from_step_results(step_results)

    def snapshot(
        self,
        step_states,
        run_status,
        current_step=None,
    ) -> ExecutionSnapshot:
        return ExecutionSnapshot(
            run_id="run-1",
            task_id="task-1",
            run_status=run_status,
            step_states=step_states,
            current_step=current_step,
            started_at="2026-09-17T16:00:00",
            finished_at="2026-09-17T16:01:00",
        )

    def test_all_steps_executed_successfully(self):
        result = self.result(
            self.step_result(
                "open_file",
                WorkflowStatus.COMPLETED,
                "opened",
                True,
            ),
            self.step_result(
                "read_file",
                WorkflowStatus.COMPLETED,
                "read",
                True,
            ),
        )

        snapshot = self.snapshot(
            {
                "step-1": StepStatus.SUCCESS,
                "step-2": StepStatus.SUCCESS,
            },
            RunStatus.COMPLETED,
        )

        summary = ExecutionSummary.from_result_and_snapshot(
            result,
            snapshot,
        )

        self.assertEqual(summary.planned_steps, 2)
        self.assertEqual(summary.executed_steps, 2)
        self.assertEqual(summary.successful_steps, 2)
        self.assertEqual(summary.failed_steps, 0)
        self.assertEqual(summary.blocked_steps, 0)
        self.assertEqual(summary.skipped_steps, 0)
        self.assertIsNone(summary.first_failure)

    def test_skipped_steps_come_from_snapshot(self):
        result = self.result(
            self.step_result(
                "open_file",
                WorkflowStatus.COMPLETED,
                "opened",
                True,
            ),
        )

        snapshot = self.snapshot(
            {
                "step-1": StepStatus.SUCCESS,
                "step-2": StepStatus.SKIPPED,
                "step-3": StepStatus.SKIPPED,
            },
            RunStatus.COMPLETED,
        )

        summary = ExecutionSummary.from_result_and_snapshot(
            result,
            snapshot,
        )

        self.assertEqual(summary.planned_steps, 3)
        self.assertEqual(summary.executed_steps, 1)
        self.assertEqual(summary.successful_steps, 1)
        self.assertEqual(summary.failed_steps, 0)
        self.assertEqual(summary.blocked_steps, 0)
        self.assertEqual(summary.skipped_steps, 2)
        self.assertIsNone(summary.first_failure)

    def test_failed_and_blocked_steps_are_taken_from_result(self):
        result = self.result(
            self.step_result(
                "open_file",
                WorkflowStatus.COMPLETED,
                "opened",
                True,
            ),
            self.step_result(
                "write_file",
                WorkflowStatus.FAILED,
                "failed",
                False,
            ),
            self.step_result(
                "run_command",
                WorkflowStatus.BLOCKED,
                "blocked",
                False,
            ),
        )

        snapshot = self.snapshot(
            {
                "step-1": StepStatus.SUCCESS,
                "step-2": StepStatus.FAILED,
                "step-3": StepStatus.FAILED,
            },
            RunStatus.FAILED,
        )

        summary = ExecutionSummary.from_result_and_snapshot(
            result,
            snapshot,
        )

        self.assertEqual(summary.planned_steps, 3)
        self.assertEqual(summary.executed_steps, 3)
        self.assertEqual(summary.successful_steps, 1)
        self.assertEqual(summary.failed_steps, 1)
        self.assertEqual(summary.blocked_steps, 1)
        self.assertEqual(summary.skipped_steps, 0)
        self.assertEqual(summary.first_failure, 1)

    def test_first_failure_is_preserved_from_result(self):
        result = self.result(
            self.step_result(
                "step_one",
                WorkflowStatus.COMPLETED,
                "ok",
                True,
            ),
            self.step_result(
                "step_two",
                WorkflowStatus.FAILED,
                "failed",
                False,
            ),
            self.step_result(
                "step_three",
                WorkflowStatus.BLOCKED,
                "blocked",
                False,
            ),
        )

        snapshot = self.snapshot(
            {
                "step-1": StepStatus.SUCCESS,
                "step-2": StepStatus.FAILED,
                "step-3": StepStatus.FAILED,
            },
            RunStatus.FAILED,
        )

        summary = ExecutionSummary.from_result_and_snapshot(
            result,
            snapshot,
        )

        self.assertEqual(
            summary.first_failure,
            result.failure_index,
        )

    def test_summary_is_immutable(self):
        result = self.result(
            self.step_result(
                "open_file",
                WorkflowStatus.COMPLETED,
                "opened",
                True,
            ),
        )

        snapshot = self.snapshot(
            {
                "step-1": StepStatus.SUCCESS,
            },
            RunStatus.COMPLETED,
        )

        summary = ExecutionSummary.from_result_and_snapshot(
            result,
            snapshot,
        )

        with self.assertRaises(AttributeError):
            summary.planned_steps = 99

    def test_tracker_snapshot_integrates_with_summary(self):
        context = WorkflowRunContext(
            run_id="run-1",
            task_id="task-1",
        )

        tracker = ExecutionTracker(
            context=context,
            step_ids=("step-1", "step-2", "step-3"),
        )

        tracker.start_run()

        tracker.start_step("step-1")
        tracker.complete_step("step-1")

        tracker.start_step("step-2")
        tracker.fail_step("step-2")

        tracker.skip_step("step-3")

        tracker.fail_run()

        snapshot = tracker.snapshot()

        result = self.result(
            self.step_result(
                "open_file",
                WorkflowStatus.COMPLETED,
                "opened",
                True,
            ),
            self.step_result(
                "write_file",
                WorkflowStatus.FAILED,
                "failed",
                False,
            ),
        )

        summary = ExecutionSummary.from_result_and_snapshot(
            result,
            snapshot,
        )

        self.assertEqual(snapshot.run_status, RunStatus.FAILED)

        self.assertEqual(
            snapshot.step_states["step-1"],
            StepStatus.SUCCESS,
        )

        self.assertEqual(
            snapshot.step_states["step-2"],
            StepStatus.FAILED,
        )

        self.assertEqual(
            snapshot.step_states["step-3"],
            StepStatus.SKIPPED,
        )

        self.assertEqual(summary.planned_steps, 3)
        self.assertEqual(summary.executed_steps, 2)
        self.assertEqual(summary.successful_steps, 1)
        self.assertEqual(summary.failed_steps, 1)
        self.assertEqual(summary.blocked_steps, 0)
        self.assertEqual(summary.skipped_steps, 1)
        self.assertEqual(summary.first_failure, 1)


if __name__ == "__main__":
    unittest.main()