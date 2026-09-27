import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.workflow_core import (
    AgentWorkflow,
    WorkflowStatus,
    WorkflowStepResult,
    WorkflowTask,
)
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from agent_workflow.workflow_service import WorkflowService
from history.history_core import HistoryStore
from permissions.reporting import PermissionRiskReport
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class WorkflowOrchestrationFailureIsolationTests(unittest.TestCase):

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)

        self.project_root = root / "project"
        self.snapshot_root = root / "snapshots"
        self.history_root = root / "history"

        self.project_root.mkdir()
        self.history_root.mkdir()

        (self.project_root / "main.py").write_text(
            "print('baseline')\n",
            encoding="utf-8",
        )

        snapshot_store = SnapshotStore(
            self.project_root,
            self.snapshot_root,
        )

        workflow = AgentWorkflow(
            HistoryStore(self.history_root),
            SnapshotService(
                self.project_root,
                store=snapshot_store,
            ),
            PermissionRiskReport(),
        )

        self.service = WorkflowService(workflow)

        self.task = WorkflowTask(
            "m16-5-3-task",
            "orchestration failure isolation",
            "M16.5.3",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _plan(self) -> WorkflowPlan:
        return WorkflowPlan(
            self.task,
            (
                WorkflowStep(
                    operation="first",
                    action=lambda: "first-ok",
                    step_id="step-001",
                ),
                WorkflowStep(
                    operation="second",
                    action=lambda: "second-ok",
                    step_id="step-002",
                ),
                WorkflowStep(
                    operation="third",
                    action=lambda: "third-ok",
                    step_id="step-003",
                ),
            ),
        )

    def test_orchestration_exception_becomes_failed_result(self) -> None:
        workflow = self.service.workflow
        successful_result = WorkflowStepResult(
            "first",
            WorkflowStatus.COMPLETED,
            "first-ok",
            True,
        )

        with patch.object(
            workflow,
            "run_step",
            side_effect=[
                successful_result,
                RuntimeError("orchestration failure"),
            ],
        ):
            result = self.service.execute(self._plan())

        self.assertEqual(result.status, WorkflowStatus.FAILED)
        self.assertFalse(result.completed_successfully)
        self.assertEqual(result.total_steps, 2)
        self.assertEqual(result.successful_steps, 1)
        self.assertEqual(result.failed_steps, 1)
        self.assertEqual(result.step_results[0], successful_result)
        self.assertEqual(
            result.step_results[1].status,
            WorkflowStatus.FAILED,
        )
        self.assertEqual(
            result.step_results[1].result,
            "RuntimeError",
        )

    def test_orchestration_exception_skips_remaining_steps(self) -> None:
        workflow = self.service.workflow
        successful_result = WorkflowStepResult(
            "first",
            WorkflowStatus.COMPLETED,
            "ok",
            True,
        )

        with patch.object(
            workflow,
            "run_step",
            side_effect=[
                successful_result,
                RuntimeError("orchestration failure"),
            ],
        ):
            self.service.execute(self._plan())

        tracker = self.service.last_execution_tracker
        self.assertIsNotNone(tracker)

        self.assertEqual(tracker.run_status, RunStatus.FAILED)
        self.assertEqual(
            tracker.step_states["step-001"],
            StepStatus.SUCCESS,
        )
        self.assertEqual(
            tracker.step_states["step-002"],
            StepStatus.FAILED,
        )
        self.assertEqual(
            tracker.step_states["step-003"],
            StepStatus.SKIPPED,
        )

    def test_orchestration_exception_preserves_run_identity(self) -> None:
        workflow = self.service.workflow
        successful_result = WorkflowStepResult(
            "first",
            WorkflowStatus.COMPLETED,
            "first-ok",
            True,
        )

        with patch.object(
            workflow,
            "run_step",
            side_effect=[
                successful_result,
                RuntimeError("orchestration failure"),
            ],
        ):
            result = self.service.execute(self._plan())

        run_context = self.service.last_run_context
        tracker = self.service.last_execution_tracker

        self.assertIsNotNone(run_context)
        self.assertIsNotNone(tracker)
        self.assertEqual(tracker.context.run_id, run_context.run_id)
        self.assertEqual(result.run_id, run_context.run_id)

    def test_orchestration_exception_does_not_execute_later_actions(self) -> None:
        workflow = self.service.workflow
        executed = []

        steps = (
            WorkflowStep(
                operation="first",
                action=lambda: executed.append("first"),
                step_id="step-001",
            ),
            WorkflowStep(
                operation="second",
                action=lambda: executed.append("second"),
                step_id="step-002",
            ),
            WorkflowStep(
                operation="third",
                action=lambda: executed.append("third"),
                step_id="step-003",
            ),
        )

        with patch.object(
            workflow,
            "run_step",
            side_effect=RuntimeError("orchestration failure"),
        ):
            result = self.service.execute(
                WorkflowPlan(self.task, steps)
            )

        self.assertEqual(result.status, WorkflowStatus.FAILED)
        self.assertEqual(executed, [])

        tracker = self.service.last_execution_tracker
        self.assertIsNotNone(tracker)
        self.assertEqual(tracker.run_status, RunStatus.FAILED)
        self.assertEqual(
            tracker.step_states["step-001"],
            StepStatus.FAILED,
        )
        self.assertEqual(
            tracker.step_states["step-002"],
            StepStatus.SKIPPED,
        )
        self.assertEqual(
            tracker.step_states["step-003"],
            StepStatus.SKIPPED,
        )


if __name__ == "__main__":
    unittest.main()
