import unittest
from unittest.mock import MagicMock

from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.workflow_core import (
    AgentWorkflow,
    WorkflowStatus,
    WorkflowTask,
    WorkflowStepResult,
)
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_run import WorkflowRunContext
from agent_workflow.workflow_service import WorkflowService


class MetadataIsolationBoundaryTests(unittest.TestCase):

    def test_workflow_result_defensively_copies_step_results(self):
        original = [
            WorkflowStepResult(
                "step-001",
                WorkflowStatus.COMPLETED,
                "done",
                True,
            )
        ]

        result = WorkflowResult.from_step_results(original)

        original.append(
            WorkflowStepResult(
                "step-002",
                WorkflowStatus.COMPLETED,
                "later",
                True,
            )
        )

        self.assertEqual(result.total_steps, 1)
        self.assertEqual(len(result.step_results), 1)

    def test_workflow_result_step_results_are_immutable(self):
        result = WorkflowResult.from_step_results(
            [
                WorkflowStepResult(
                    "step-001",
                    WorkflowStatus.COMPLETED,
                    "done",
                    True,
                )
            ]
        )

        self.assertIsInstance(result.step_results, tuple)

        with self.assertRaises(AttributeError):
            result.step_results.append("invalid")

    def test_snapshot_step_states_are_read_only(self):
        snapshot = ExecutionSnapshot(
            run_id="run-001",
            task_id="task-001",
            run_status=RunStatus.RUNNING,
            step_states={
                "step-001": StepStatus.PENDING,
            },
            current_step=None,
            started_at=None,
            finished_at=None,
        )

        with self.assertRaises(TypeError):
            snapshot.step_states["step-001"] = StepStatus.SUCCESS

    def test_snapshot_isolated_from_tracker_state(self):
        context = WorkflowRunContext.create(
            WorkflowTask(
                "task-m16-6-5",
                "Snapshot isolation test",
            )
        )

        tracker = ExecutionTracker(
            context,
            ("step-001", "step-002"),
        )

        tracker.start_run()
        tracker.start_step("step-001")

        snapshot = tracker.snapshot()

        tracker.complete_step("step-001")
        tracker.start_step("step-002")

        self.assertEqual(
            snapshot.step_states["step-001"],
            StepStatus.RUNNING,
        )
        self.assertEqual(
            snapshot.step_states["step-002"],
            StepStatus.PENDING,
        )

        self.assertEqual(
            tracker.step_states["step-001"],
            StepStatus.SUCCESS,
        )
        self.assertEqual(
            tracker.step_states["step-002"],
            StepStatus.RUNNING,
        )

    def test_service_result_metadata_does_not_change_after_execution(self):
        workflow = AgentWorkflow(
            history_store=MagicMock(),
            snapshot_service=MagicMock(),
        )
        service = WorkflowService(workflow)

        task = WorkflowTask(
            "task-m16-6-5-service",
            "Service metadata isolation",
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

        result = service.execute(plan)

        original_run_id = result.run_id
        original_total = result.total_steps
        original_successful = result.successful_steps

        tracker = service.last_execution_tracker
        self.assertIsNotNone(tracker)

        tracker.snapshot()

        self.assertEqual(result.run_id, original_run_id)
        self.assertEqual(result.total_steps, original_total)
        self.assertEqual(
            result.successful_steps,
            original_successful,
        )


if __name__ == "__main__":
    unittest.main()
