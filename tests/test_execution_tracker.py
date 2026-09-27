import unittest
from datetime import datetime, timezone

from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.workflow_run import WorkflowRunContext


class ExecutionTrackerTests(unittest.TestCase):

    def _context(self) -> WorkflowRunContext:
        return WorkflowRunContext(
            run_id="run-001",
            task_id="task-001",
        )

    def _tracker(self) -> ExecutionTracker:
        return ExecutionTracker(
            self._context(),
            ("step-001", "step-002"),
        )

    def test_initial_state(self):
        tracker = self._tracker()

        self.assertEqual(tracker.context, self._context())
        self.assertEqual(tracker.run_status, RunStatus.CREATED)
        self.assertEqual(
            dict(tracker.step_states),
            {
                "step-001": StepStatus.PENDING,
                "step-002": StepStatus.PENDING,
            },
        )
        self.assertIsNone(tracker.current_step)
        self.assertIsNone(tracker.started_at)
        self.assertIsNone(tracker.finished_at)

    def test_invalid_step_ids(self):
        with self.assertRaises(ValueError):
            ExecutionTracker(self._context(), ("",))

        with self.assertRaises(ValueError):
            ExecutionTracker(self._context(), (1,))

        with self.assertRaises(ValueError):
            ExecutionTracker(
                self._context(),
                ("step-001", "step-001"),
            )

    def test_non_tuple_step_ids_are_accepted(self):
        tracker = ExecutionTracker(
            self._context(),
            ["step-001", "step-002"],
        )

        self.assertEqual(
            set(tracker.step_states),
            {"step-001", "step-002"},
        )

    def test_start_run(self):
        tracker = self._tracker()

        tracker.start_run()

        self.assertEqual(tracker.run_status, RunStatus.RUNNING)
        self.assertIsInstance(tracker.started_at, datetime)
        self.assertEqual(tracker.started_at.tzinfo, timezone.utc)
        self.assertIsNone(tracker.finished_at)

    def test_start_run_twice_fails(self):
        tracker = self._tracker()

        tracker.start_run()

        with self.assertRaises(RuntimeError):
            tracker.start_run()

    def test_start_step(self):
        tracker = self._tracker()
        tracker.start_run()

        tracker.start_step("step-001")

        self.assertEqual(
            tracker.step_states["step-001"],
            StepStatus.RUNNING,
        )
        self.assertEqual(tracker.current_step, "step-001")

    def test_start_step_requires_existing_step(self):
        tracker = self._tracker()
        tracker.start_run()

        with self.assertRaises(KeyError):
            tracker.start_step("missing")

    def test_start_step_requires_running_run(self):
        tracker = self._tracker()

        with self.assertRaises(RuntimeError):
            tracker.start_step("step-001")

    def test_only_one_step_can_run(self):
        tracker = self._tracker()
        tracker.start_run()
        tracker.start_step("step-001")

        with self.assertRaises(RuntimeError):
            tracker.start_step("step-002")

    def test_complete_step(self):
        tracker = self._tracker()
        tracker.start_run()
        tracker.start_step("step-001")

        tracker.complete_step("step-001")

        self.assertEqual(
            tracker.step_states["step-001"],
            StepStatus.SUCCESS,
        )
        self.assertIsNone(tracker.current_step)

    def test_complete_step_requires_running_step(self):
        tracker = self._tracker()
        tracker.start_run()

        with self.assertRaises(RuntimeError):
            tracker.complete_step("step-001")

    def test_fail_step(self):
        tracker = self._tracker()
        tracker.start_run()
        tracker.start_step("step-001")

        tracker.fail_step("step-001")

        self.assertEqual(
            tracker.step_states["step-001"],
            StepStatus.FAILED,
        )
        self.assertIsNone(tracker.current_step)

    def test_fail_step_requires_running_step(self):
        tracker = self._tracker()
        tracker.start_run()

        with self.assertRaises(RuntimeError):
            tracker.fail_step("step-001")

    def test_skip_step(self):
        tracker = self._tracker()
        tracker.start_run()

        tracker.skip_step("step-001")

        self.assertEqual(
            tracker.step_states["step-001"],
            StepStatus.SKIPPED,
        )

    def test_skip_step_requires_pending_step(self):
        tracker = self._tracker()
        tracker.start_run()
        tracker.start_step("step-001")

        with self.assertRaises(RuntimeError):
            tracker.skip_step("step-001")

        tracker.complete_step("step-001")

        with self.assertRaises(RuntimeError):
            tracker.skip_step("step-001")

    def test_complete_run(self):
        tracker = self._tracker()
        tracker.start_run()
        tracker.start_step("step-001")
        tracker.complete_step("step-001")

        tracker.complete_run()

        self.assertEqual(
            tracker.run_status,
            RunStatus.COMPLETED,
        )
        self.assertIsNotNone(tracker.started_at)
        self.assertIsNotNone(tracker.finished_at)
        self.assertEqual(
            tracker.started_at.tzinfo,
            timezone.utc,
        )
        self.assertEqual(
            tracker.finished_at.tzinfo,
            timezone.utc,
        )
        self.assertGreaterEqual(
            tracker.finished_at,
            tracker.started_at,
        )
        self.assertIsNone(tracker.current_step)

    def test_complete_run_while_step_running_fails(self):
        tracker = self._tracker()
        tracker.start_run()
        tracker.start_step("step-001")

        with self.assertRaises(RuntimeError):
            tracker.complete_run()

        self.assertEqual(
            tracker.run_status,
            RunStatus.RUNNING,
        )
        self.assertIsNone(tracker.finished_at)
        self.assertEqual(
            tracker.current_step,
            "step-001",
        )

    def test_fail_run(self):
        tracker = self._tracker()
        tracker.start_run()

        tracker.fail_run()

        self.assertEqual(
            tracker.run_status,
            RunStatus.FAILED,
        )
        self.assertIsNotNone(tracker.started_at)
        self.assertIsNotNone(tracker.finished_at)
        self.assertEqual(
            tracker.started_at.tzinfo,
            timezone.utc,
        )
        self.assertEqual(
            tracker.finished_at.tzinfo,
            timezone.utc,
        )
        self.assertGreaterEqual(
            tracker.finished_at,
            tracker.started_at,
        )
        self.assertIsNone(tracker.current_step)

    def test_fail_run_while_step_running_fails(self):
        tracker = self._tracker()
        tracker.start_run()
        tracker.start_step("step-001")

        with self.assertRaises(RuntimeError):
            tracker.fail_run()

        self.assertEqual(
            tracker.run_status,
            RunStatus.RUNNING,
        )
        self.assertIsNone(tracker.finished_at)
        self.assertEqual(
            tracker.current_step,
            "step-001",
        )

    def test_completed_run_cannot_change(self):
        tracker = self._tracker()
        tracker.start_run()
        tracker.complete_run()

        with self.assertRaises(RuntimeError):
            tracker.complete_run()

        with self.assertRaises(RuntimeError):
            tracker.fail_run()

        with self.assertRaises(RuntimeError):
            tracker.start_step("step-001")

    def test_failed_run_cannot_change(self):
        tracker = self._tracker()
        tracker.start_run()
        tracker.fail_run()

        with self.assertRaises(RuntimeError):
            tracker.complete_run()

        with self.assertRaises(RuntimeError):
            tracker.fail_run()

        with self.assertRaises(RuntimeError):
            tracker.start_step("step-001")

    def test_snapshot_captures_running_state(self):
        tracker = self._tracker()
        tracker.start_run()
        tracker.start_step("step-001")

        snapshot = tracker.snapshot()

        self.assertIsInstance(snapshot, ExecutionSnapshot)
        self.assertEqual(snapshot.run_id, "run-001")
        self.assertEqual(snapshot.task_id, "task-001")
        self.assertEqual(snapshot.run_status, RunStatus.RUNNING)
        self.assertEqual(
            snapshot.step_states["step-001"],
            StepStatus.RUNNING,
        )
        self.assertEqual(
            snapshot.step_states["step-002"],
            StepStatus.PENDING,
        )
        self.assertEqual(snapshot.current_step, "step-001")
        self.assertEqual(snapshot.started_at, tracker.started_at)
        self.assertIsNone(snapshot.finished_at)

    def test_snapshot_is_a_point_in_time_observation(self):
        tracker = self._tracker()
        tracker.start_run()

        first = tracker.snapshot()

        tracker.start_step("step-001")
        tracker.complete_step("step-001")

        second = tracker.snapshot()

        self.assertEqual(
            first.run_status,
            RunStatus.RUNNING,
        )
        self.assertIsNone(first.current_step)
        self.assertEqual(
            first.step_states["step-001"],
            StepStatus.PENDING,
        )

        self.assertEqual(
            second.step_states["step-001"],
            StepStatus.SUCCESS,
        )
        self.assertIsNone(second.current_step)

    def test_snapshot_returns_execution_snapshot(self):
        tracker = self._tracker()

        snapshot = tracker.snapshot()

        self.assertIsInstance(snapshot, ExecutionSnapshot)

    def test_snapshot_is_immutable(self):
        tracker = self._tracker()
        tracker.start_run()

        snapshot = tracker.snapshot()

        with self.assertRaises((AttributeError, TypeError)):
            snapshot.run_id = "changed"

    def test_step_states_are_read_only(self):
        tracker = self._tracker()

        states = tracker.step_states

        with self.assertRaises(TypeError):
            states["step-001"] = StepStatus.SUCCESS


if __name__ == "__main__":
    unittest.main()