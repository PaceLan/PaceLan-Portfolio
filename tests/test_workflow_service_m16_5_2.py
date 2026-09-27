import tempfile
import unittest
from pathlib import Path

from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.workflow_core import AgentWorkflow, WorkflowStatus, WorkflowTask
from agent_workflow.workflow_plan import WorkflowStep
from agent_workflow.workflow_service import WorkflowService
from history.history_core import HistoryStore
from permissions.reporting import PermissionRiskReport
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class WorkflowServiceM1652Tests(unittest.TestCase):

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
            "m16-5-2-task",
            "failure isolation test",
            "M16.5.2",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_action_exception_is_normalized_without_leaking(self) -> None:
        executed = []

        def failing_action() -> str:
            executed.append("failing")
            raise RuntimeError("controlled failure")

        plan = self.service.build(
            self.task,
            (
                WorkflowStep(
                    "failing step",
                    failing_action,
                    step_id="step-001",
                ),
                WorkflowStep(
                    "after failure",
                    lambda: executed.append("after") or "must not run",
                    step_id="step-002",
                ),
            ),
        )

        try:
            result = self.service.execute(plan)
        except RuntimeError as error:
            self.fail(
                f"WorkflowService leaked Action exception: {error}"
            )

        self.assertEqual(executed, ["failing"])
        self.assertEqual(result.status, WorkflowStatus.FAILED)
        self.assertFalse(result.completed_successfully)

    def test_failed_step_and_later_skipped_steps_are_consistent(self) -> None:
        def failing_action() -> str:
            raise ValueError("normalized failure")

        plan = self.service.build(
            self.task,
            (
                WorkflowStep(
                    "failing step",
                    failing_action,
                    step_id="step-001",
                ),
                WorkflowStep(
                    "later step one",
                    lambda: "must not run",
                    step_id="step-002",
                ),
                WorkflowStep(
                    "later step two",
                    lambda: "must not run",
                    step_id="step-003",
                ),
            ),
        )

        result = self.service.execute(plan)
        tracker = self.service.last_execution_tracker

        self.assertIsNotNone(tracker)

        self.assertEqual(
            result.status,
            WorkflowStatus.FAILED,
        )

        self.assertEqual(
            result.failed_steps,
            1,
        )

        self.assertEqual(
            result.step_results[0].status,
            WorkflowStatus.FAILED,
        )

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

    def test_run_result_and_tracker_share_same_run_id(self) -> None:
        plan = self.service.build(
            self.task,
            (
                WorkflowStep(
                    "failing step",
                    lambda: (_ for _ in ()).throw(
                        RuntimeError("controlled failure")
                    ),
                    step_id="step-001",
                ),
                WorkflowStep(
                    "later step",
                    lambda: "must not run",
                    step_id="step-002",
                ),
            ),
        )

        result = self.service.execute(plan)

        run_context = self.service.last_run_context
        tracker = self.service.last_execution_tracker

        self.assertIsNotNone(run_context)
        self.assertIsNotNone(tracker)

        self.assertEqual(
            run_context.run_id,
            tracker.context.run_id,
        )

        self.assertEqual(
            tracker.run_status,
            RunStatus.FAILED,
        )

        self.assertEqual(
            result.status,
            WorkflowStatus.FAILED,
        )

    def test_success_path_remains_unchanged(self) -> None:
        executed = []

        plan = self.service.build(
            self.task,
            (
                WorkflowStep(
                    "first success",
                    lambda: executed.append("one") or "one",
                    step_id="step-001",
                ),
                WorkflowStep(
                    "second success",
                    lambda: executed.append("two") or "two",
                    step_id="step-002",
                ),
            ),
        )

        result = self.service.execute(plan)
        tracker = self.service.last_execution_tracker

        self.assertEqual(
            executed,
            ["one", "two"],
        )

        self.assertEqual(
            result.status,
            WorkflowStatus.COMPLETED,
        )

        self.assertTrue(
            result.completed_successfully,
        )

        self.assertIsNotNone(tracker)

        self.assertEqual(
            tracker.run_status,
            RunStatus.COMPLETED,
        )

        self.assertEqual(
            tracker.step_states["step-001"],
            StepStatus.SUCCESS,
        )

        self.assertEqual(
            tracker.step_states["step-002"],
            StepStatus.SUCCESS,
        )


if __name__ == "__main__":
    unittest.main()