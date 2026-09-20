from datetime import datetime, timezone
import unittest

from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.workflow_run import WorkflowRunContext


class ExecutionTrackerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.context = WorkflowRunContext(
            run_id="run-1",
            task_id="task-1",
        )
        self.tracker = ExecutionTracker(
            self.context,
            ("step-1", "step-2"),
        )

    def test_initial_state(self) -> None:
        self.assertIs(self.tracker.context, self.context)
        self.assertIs(self.tracker.run_status, RunStatus.CREATED)
        self.assertEqual(
            self.tracker.step_states,
            {
                "step-1": StepStatus.PENDING,
                "step-2": StepStatus.PENDING,
            },
        )
        self.assertIsNone(self.tracker.current_step)
        self.assertIsNone(self.tracker.started_at)
        self.assertIsNone(self.tracker.finished_at)

    def test_step_states_are_read_only(self) -> None:
        with self.assertRaises(TypeError):
            self.tracker.step_states["step-1"] = StepStatus.RUNNING

    def test_start_run(self) -> None:
        before = datetime.now(timezone.utc)

        self.tracker.start_run()

        after = datetime.now(timezone.utc)

        self.assertIs(self.tracker.run_status, RunStatus.RUNNING)
        self.assertIsNotNone(self.tracker.started_at)
        self.assertGreaterEqual(self.tracker.started_at, before)
        self.assertLessEqual(self.tracker.started_at, after)
        self.assertIsNone(self.tracker.finished_at)

    def test_start_run_twice_fails(self) -> None:
        self.tracker.start_run()

        with self.assertRaises(RuntimeError):
            self.tracker.start_run()

    def test_start_step(self) -> None:
        self.tracker.start_run()
        self.tracker.start_step("step-1")

        self.assertIs(self.tracker.run_status, RunStatus.RUNNING)
        self.assertEqual(self.tracker.current_step, "step-1")
        self.assertIs(
            self.tracker.step_states["step-1"],
            StepStatus.RUNNING,
        )

    def test_start_step_requires_existing_step(self) -> None:
        self.tracker.start_run()

        with self.assertRaises(KeyError):
            self.tracker.start_step("missing")

    def test_start_step_requires_running_run(self) -> None:
        with self.assertRaises(RuntimeError):
            self.tracker.start_step("step-1")

    def test_only_one_step_can_run(self) -> None:
        self.tracker.start_run()
        self.tracker.start_step("step-1")

        with self.assertRaises(RuntimeError):
            self.tracker.start_step("step-2")

    def test_complete_step(self) -> None:
        self.tracker.start_run()
        self.tracker.start_step("step-1")
        self.tracker.complete_step("step-1")

        self.assertIs(
            self.tracker.step_states["step-1"],
            StepStatus.SUCCESS,
        )
        self.assertIsNone(self.tracker.current_step)

    def test_complete_step_requires_running_step(self) -> None:
        self.tracker.start_run()

        with self.assertRaises(RuntimeError):
            self.tracker.complete_step("step-1")

    def test_fail_step(self) -> None:
        self.tracker.start_run()
        self.tracker.start_step("step-1")
        self.tracker.fail_step("step-1")

        self.assertIs(
            self.tracker.step_states["step-1"],
            StepStatus.FAILED,
        )
        self.assertIsNone(self.tracker.current_step)

    def test_fail_step_requires_running_step(self) -> None:
        self.tracker.start_run()

        with self.assertRaises(RuntimeError):
            self.tracker.fail_step("step-1")

    def test_skip_step(self) -> None:
        self.tracker.start_run()
        self.tracker.skip_step("step-1")

        self.assertIs(
            self.tracker.step_states["step-1"],
            StepStatus.SKIPPED,
        )
        self.assertIsNone(self.tracker.current_step)

    def test_skip_step_requires_pending_step(self) -> None:
        self.tracker.start_run()
        self.tracker.start_step("step-1")

        with self.assertRaises(RuntimeError):
            self.tracker.skip_step("step-1")

    def test_complete_run(self) -> None:
        self.tracker.start_run()
        self.tracker.start_step("step-1")
        self.tracker.complete_step("step-1")
        self.tracker.complete_run()

        self.assertIs(
            self.tracker.run_status,
            RunStatus.COMPLETED,
        )
        self.assertIsNotNone(self.tracker.finished_at)
        self.assertIsNone(self.tracker.current_step)

    def test_complete_run_while_step_running_fails(self) -> None:
        self.tracker.start_run()
        self.tracker.start_step("step-1")

        with self.assertRaises(RuntimeError):
            self.tracker.complete_run()

    def test_fail_run(self) -> None:
        self.tracker.start_run()
        self.tracker.fail_run()

        self.assertIs(
            self.tracker.run_status,
            RunStatus.FAILED,
        )
        self.assertIsNotNone(self.tracker.finished_at)
        self.assertIsNone(self.tracker.current_step)

    def test_fail_run_while_step_running_fails(self) -> None:
        self.tracker.start_run()
        self.tracker.start_step("step-1")

        with self.assertRaises(RuntimeError):
            self.tracker.fail_run()

    def test_completed_run_cannot_change(self) -> None:
        self.tracker.start_run()
        self.tracker.complete_run()

        with self.assertRaises(RuntimeError):
            self.tracker.complete_run()

    def test_failed_run_cannot_change(self) -> None:
        self.tracker.start_run()
        self.tracker.fail_run()

        with self.assertRaises(RuntimeError):
            self.tracker.fail_run()

    def test_invalid_step_ids(self) -> None:
        with self.assertRaises(ValueError):
            ExecutionTracker(self.context, ("",))

        with self.assertRaises(ValueError):
            ExecutionTracker(self.context, ("step-1", "step-1"))

    def test_snapshot_returns_execution_snapshot(self) -> None:
        snapshot = self.tracker.snapshot()

        self.assertIsInstance(snapshot, ExecutionSnapshot)
        self.assertEqual(snapshot.run_id, "run-1")
        self.assertEqual(snapshot.task_id, "task-1")
        self.assertIs(snapshot.run_status, RunStatus.CREATED)
        self.assertEqual(
            snapshot.step_states,
            {
                "step-1": StepStatus.PENDING,
                "step-2": StepStatus.PENDING,
            },
        )
        self.assertIsNone(snapshot.current_step)
        self.assertIsNone(snapshot.started_at)
        self.assertIsNone(snapshot.finished_at)

    def test_snapshot_captures_running_state(self) -> None:
        self.tracker.start_run()
        self.tracker.start_step("step-1")

        snapshot = self.tracker.snapshot()

        self.assertIs(snapshot.run_status, RunStatus.RUNNING)
        self.assertEqual(snapshot.current_step, "step-1")
        self.assertIsNotNone(snapshot.started_at)
        self.assertIsNone(snapshot.finished_at)
        self.assertIs(
            snapshot.step_states["step-1"],
            StepStatus.RUNNING,
        )

    def test_snapshot_is_immutable(self) -> None:
        snapshot = self.tracker.snapshot()

        with self.assertRaises(TypeError):
            snapshot.step_states["step-1"] = StepStatus.SUCCESS

    def test_snapshot_is_a_point_in_time_observation(self) -> None:
        self.tracker.start_run()
        snapshot = self.tracker.snapshot()

        self.tracker.start_step("step-1")

        self.assertIsNone(snapshot.current_step)
        self.assertIs(
            snapshot.step_states["step-1"],
            StepStatus.PENDING,
        )

    def test_non_tuple_step_ids_are_accepted(self) -> None:
        tracker = ExecutionTracker(
            self.context,
            ["step-1", "step-2"],
        )

        self.assertEqual(
            tracker.step_states,
            {
                "step-1": StepStatus.PENDING,
                "step-2": StepStatus.PENDING,
            },
        )


if __name__ == "__main__":
    unittest.main()