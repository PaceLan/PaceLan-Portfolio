import unittest
from datetime import datetime, timezone

from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.workflow_run import WorkflowRunContext


class ExecutionSnapshotTemporalTests(unittest.TestCase):

    def _tracker(self) -> ExecutionTracker:
        context = WorkflowRunContext(
            run_id="run-temporal-001",
            task_id="task-temporal-001",
        )
        return ExecutionTracker(context, ("step-001",))

    def test_initial_state_has_no_temporal_metadata(self):
        tracker = self._tracker()

        self.assertIsNone(tracker.started_at)
        self.assertIsNone(tracker.finished_at)

        snapshot = tracker.snapshot()

        self.assertEqual(snapshot.run_status, RunStatus.CREATED)
        self.assertIsNone(snapshot.started_at)
        self.assertIsNone(snapshot.finished_at)

    def test_running_state_has_started_at_but_no_finished_at(self):
        tracker = self._tracker()
        tracker.start_run()

        self.assertIsInstance(tracker.started_at, datetime)
        self.assertEqual(tracker.started_at.tzinfo, timezone.utc)
        self.assertIsNone(tracker.finished_at)

        snapshot = tracker.snapshot()

        self.assertEqual(snapshot.run_status, RunStatus.RUNNING)
        self.assertIsNotNone(snapshot.started_at)
        self.assertIsNone(snapshot.finished_at)

    def test_completed_state_has_both_timestamps(self):
        tracker = self._tracker()
        tracker.start_run()

        started_at = tracker.started_at

        tracker.complete_run()

        self.assertIsNotNone(started_at)
        self.assertIsNotNone(tracker.finished_at)
        self.assertEqual(started_at.tzinfo, timezone.utc)
        self.assertEqual(tracker.finished_at.tzinfo, timezone.utc)
        self.assertGreaterEqual(tracker.finished_at, started_at)

        snapshot = tracker.snapshot()

        self.assertEqual(snapshot.run_status, RunStatus.COMPLETED)
        self.assertEqual(snapshot.started_at, started_at)
        self.assertEqual(snapshot.finished_at, tracker.finished_at)

    def test_failed_state_has_both_timestamps(self):
        tracker = self._tracker()
        tracker.start_run()

        started_at = tracker.started_at

        tracker.fail_run()

        self.assertIsNotNone(started_at)
        self.assertIsNotNone(tracker.finished_at)
        self.assertEqual(started_at.tzinfo, timezone.utc)
        self.assertEqual(tracker.finished_at.tzinfo, timezone.utc)
        self.assertGreaterEqual(tracker.finished_at, started_at)

        snapshot = tracker.snapshot()

        self.assertEqual(snapshot.run_status, RunStatus.FAILED)
        self.assertEqual(snapshot.started_at, started_at)
        self.assertEqual(snapshot.finished_at, tracker.finished_at)

    def test_started_at_is_stable_after_run_starts(self):
        tracker = self._tracker()
        tracker.start_run()

        started_at = tracker.started_at

        tracker.start_step("step-001")
        tracker.complete_step("step-001")

        self.assertEqual(tracker.started_at, started_at)

    def test_finished_at_is_not_set_while_running(self):
        tracker = self._tracker()
        tracker.start_run()

        tracker.start_step("step-001")

        snapshot = tracker.snapshot()

        self.assertEqual(snapshot.run_status, RunStatus.RUNNING)
        self.assertIsNotNone(snapshot.started_at)
        self.assertIsNone(snapshot.finished_at)


if __name__ == "__main__":
    unittest.main()
