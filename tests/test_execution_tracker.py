import unittest
from datetime import timezone
from types import MappingProxyType

from agent_workflow.execution_tracker import (
    ExecutionTracker,
    RunStatus,
    StepStatus,
)
from agent_workflow.workflow_run import WorkflowRunContext


class ExecutionTrackerTests(unittest.TestCase):

    def make_context(self):
        return WorkflowRunContext(
            run_id="run-1",
            task_id="task-1",
        )

    def make_tracker(self):
        return ExecutionTracker(
            self.make_context(),
            ("step-1", "step-2", "step-3"),
        )

    def test_initial_state(self):
        tracker = self.make_tracker()

        self.assertIs(tracker.run_status, RunStatus.CREATED)
        self.assertIsNone(tracker.current_step)
        self.assertIsNone(tracker.started_at)
        self.assertIsNone(tracker.finished_at)
        self.assertEqual(
            dict(tracker.step_states),
            {
                "step-1": StepStatus.PENDING,
                "step-2": StepStatus.PENDING,
                "step-3": StepStatus.PENDING,
            },
        )

    def test_context_is_original_context(self):
        context = self.make_context()
        tracker = ExecutionTracker(context, ("step-1",))

        self.assertIs(tracker.context, context)

    def test_snapshot_returns_execution_snapshot(self):
        from agent_workflow.execution_snapshot import ExecutionSnapshot

        tracker = self.make_tracker()

        snapshot = tracker.snapshot()

        self.assertIsInstance(snapshot, ExecutionSnapshot)

    def test_snapshot_initial_state(self):
        tracker = self.make_tracker()

        snapshot = tracker.snapshot()

        self.assertEqual(snapshot.run_id, "run-1")
        self.assertEqual(snapshot.task_id, "task-1")
        self.assertIs(snapshot.run_status, RunStatus.CREATED)
        self.assertEqual(
            dict(snapshot.step_states),
            {
                "step-1": StepStatus.PENDING,
                "step-2": StepStatus.PENDING,
                "step-3": StepStatus.PENDING,
            },
        )
        self.assertIsNone(snapshot.current_step)
        self.assertIsNone(snapshot.started_at)
        self.assertIsNone(snapshot.finished_at)

    def test_snapshot_running_state(self):
        tracker = self.make_tracker()
        tracker.start_run()
        tracker.start_step("step-1")

        snapshot = tracker.snapshot()

        self.assertIs(snapshot.run_status, RunStatus.RUNNING)
        self.assertEqual(snapshot.current_step, "step-1")
        self.assertIsNotNone(snapshot.started_at)
        self.assertIsNone(snapshot.finished_at)
        self.assertIs(
            snapshot.step_states["step-1"],
            StepStatus.RUNNING,
        )

    def test_snapshot_uses_context_identity(self):
        context = self.make_context()
        tracker = ExecutionTracker(context, ("step-1",))

        snapshot = tracker.snapshot()

        self.assertEqual(snapshot.run_id, context.run_id)
        self.assertEqual(snapshot.task_id, context.task_id)

    def test_old_snapshot_is_independent_of_tracker_changes(self):
        tracker = self.make_tracker()
        tracker.start_run()
        tracker.start_step("step-1")

        snapshot = tracker.snapshot()

        tracker.complete_step("step-1")
        tracker.start_step("step-2")

        self.assertIs(
            snapshot.run_status,
            RunStatus.RUNNING,
        )
        self.assertEqual(snapshot.current_step, "step-1")
        self.assertIs(
            snapshot.step_states["step-1"],
            StepStatus.RUNNING,
        )
        self.assertIs(
            snapshot.step_states["step-2"],
            StepStatus.PENDING,
        )

    def test_snapshot_step_states_are_read_only(self):
        tracker = self.make_tracker()

        snapshot = tracker.snapshot()

        with self.assertRaises(TypeError):
            snapshot.step_states["step-1"] = StepStatus.SUCCESS

    def test_start_run(self):
        tracker = self.make_tracker()

        tracker.start_run()

        self.assertIs(tracker.run_status, RunStatus.RUNNING)
        self.assertIsNotNone(tracker.started_at)
        self.assertIsNone(tracker.finished_at)
        self.assertIsNotNone(tracker.started_at.tzinfo)

    def test_start_run_twice_is_invalid(self):
        tracker = self.make_tracker()
        tracker.start_run()

        with self.assertRaises(RuntimeError):
            tracker.start_run()

    def test_start_step(self):
        tracker = self.make_tracker()
        tracker.start_run()

        tracker.start_step("step-1")

        self.assertIs(tracker.step_states["step-1"], StepStatus.RUNNING)
        self.assertEqual(tracker.current_step, "step-1")

    def test_start_step_requires_running_run(self):
        tracker = self.make_tracker()

        with self.assertRaises(RuntimeError):
            tracker.start_step("step-1")

    def test_only_one_step_can_run(self):
        tracker = self.make_tracker()
        tracker.start_run()
        tracker.start_step("step-1")

        with self.assertRaises(RuntimeError):
            tracker.start_step("step-2")

    def test_start_step_twice_is_invalid(self):
        tracker = self.make_tracker()
        tracker.start_run()
        tracker.start_step("step-1")

        with self.assertRaises(RuntimeError):
            tracker.start_step("step-1")

    def test_complete_step(self):
        tracker = self.make_tracker()
        tracker.start_run()
        tracker.start_step("step-1")

        tracker.complete_step("step-1")

        self.assertIs(
            tracker.step_states["step-1"],
            StepStatus.SUCCESS,
        )
        self.assertIsNone(tracker.current_step)
        self.assertIs(tracker.run_status, RunStatus.RUNNING)
        self.assertIsNone(tracker.finished_at)

    def test_complete_step_does_not_start_next_step(self):
        tracker = self.make_tracker()
        tracker.start_run()
        tracker.start_step("step-1")
        tracker.complete_step("step-1")

        self.assertIs(
            tracker.step_states["step-2"],
            StepStatus.PENDING,
        )
        self.assertIsNone(tracker.current_step)

    def test_fail_step(self):
        tracker = self.make_tracker()
        tracker.start_run()
        tracker.start_step("step-1")

        tracker.fail_step("step-1")

        self.assertIs(
            tracker.step_states["step-1"],
            StepStatus.FAILED,
        )
        self.assertIsNone(tracker.current_step)
        self.assertIs(tracker.run_status, RunStatus.RUNNING)

    def test_skip_step(self):
        tracker = self.make_tracker()
        tracker.start_run()

        tracker.skip_step("step-1")

        self.assertIs(
            tracker.step_states["step-1"],
            StepStatus.SKIPPED,
        )
        self.assertIsNone(tracker.current_step)

    def test_running_step_cannot_be_skipped(self):
        tracker = self.make_tracker()
        tracker.start_run()
        tracker.start_step("step-1")

        with self.assertRaises(RuntimeError):
            tracker.skip_step("step-1")

    def test_complete_run_requires_no_running_step(self):
        tracker = self.make_tracker()
        tracker.start_run()
        tracker.start_step("step-1")

        with self.assertRaises(RuntimeError):
            tracker.complete_run()

        self.assertIs(tracker.run_status, RunStatus.RUNNING)

    def test_complete_run(self):
        tracker = self.make_tracker()
        tracker.start_run()
        tracker.start_step("step-1")
        tracker.complete_step("step-1")

        tracker.complete_run()

        self.assertIs(tracker.run_status, RunStatus.COMPLETED)
        self.assertIsNone(tracker.current_step)
        self.assertIsNotNone(tracker.finished_at)
        self.assertIsNotNone(tracker.started_at)
        self.assertGreaterEqual(
            tracker.finished_at,
            tracker.started_at,
        )
        self.assertIsNotNone(tracker.finished_at.tzinfo)

    def test_fail_run(self):
        tracker = self.make_tracker()
        tracker.start_run()

        tracker.fail_run()

        self.assertIs(tracker.run_status, RunStatus.FAILED)
        self.assertIsNone(tracker.current_step)
        self.assertIsNotNone(tracker.finished_at)
        self.assertGreaterEqual(
            tracker.finished_at,
            tracker.started_at,
        )

    def test_fail_run_requires_no_running_step(self):
        tracker = self.make_tracker()
        tracker.start_run()
        tracker.start_step("step-1")

        with self.assertRaises(RuntimeError):
            tracker.fail_run()

    def test_terminal_completed_state_is_locked(self):
        tracker = self.make_tracker()
        tracker.start_run()
        tracker.complete_run()

        mutations = (
            lambda: tracker.start_run(),
            lambda: tracker.start_step("step-1"),
            lambda: tracker.complete_step("step-1"),
            lambda: tracker.fail_step("step-1"),
            lambda: tracker.skip_step("step-1"),
            lambda: tracker.complete_run(),
            lambda: tracker.fail_run(),
        )

        for mutation in mutations:
            with self.assertRaises((RuntimeError, KeyError)):
                mutation()

    def test_terminal_failed_state_is_locked(self):
        tracker = self.make_tracker()
        tracker.start_run()
        tracker.fail_run()

        mutations = (
            lambda: tracker.start_run(),
            lambda: tracker.start_step("step-1"),
            lambda: tracker.complete_step("step-1"),
            lambda: tracker.fail_step("step-1"),
            lambda: tracker.skip_step("step-1"),
            lambda: tracker.complete_run(),
            lambda: tracker.fail_run(),
        )

        for mutation in mutations:
            with self.assertRaises((RuntimeError, KeyError)):
                mutation()

    def test_unknown_step_raises_key_error(self):
        tracker = self.make_tracker()
        tracker.start_run()

        operations = (
            lambda: tracker.start_step("step-999"),
            lambda: tracker.complete_step("step-999"),
            lambda: tracker.fail_step("step-999"),
            lambda: tracker.skip_step("step-999"),
        )

        for operation in operations:
            with self.assertRaises(KeyError):
                operation()

    def test_duplicate_step_ids_raise_value_error(self):
        with self.assertRaises(ValueError):
            ExecutionTracker(
                self.make_context(),
                ("step-1", "step-1"),
            )

    def test_empty_step_id_raises_value_error(self):
        with self.assertRaises(ValueError):
            ExecutionTracker(
                self.make_context(),
                ("step-1", ""),
            )

    def test_non_string_step_id_raises_value_error(self):
        with self.assertRaises(ValueError):
            ExecutionTracker(
                self.make_context(),
                ("step-1", 123),
            )

    def test_empty_step_sequence_is_allowed_by_type_but_has_no_steps(self):
        tracker = ExecutionTracker(
            self.make_context(),
            (),
        )

        self.assertEqual(dict(tracker.step_states), {})

    def test_step_states_are_read_only(self):
        tracker = self.make_tracker()

        states = tracker.step_states

        self.assertIsInstance(states, MappingProxyType)

        with self.assertRaises(TypeError):
            states["step-1"] = StepStatus.FAILED

        self.assertIs(
            tracker.step_states["step-1"],
            StepStatus.PENDING,
        )

    def test_step_state_mapping_is_fresh_view_of_internal_state(self):
        tracker = self.make_tracker()
        states_before = tracker.step_states

        tracker.start_run()
        tracker.start_step("step-1")

        self.assertIs(
            states_before["step-1"],
            StepStatus.RUNNING,
        )
        self.assertIs(
            tracker.step_states["step-1"],
            StepStatus.RUNNING,
        )

    def test_full_lifecycle(self):
        tracker = self.make_tracker()

        tracker.start_run()

        tracker.start_step("step-1")
        tracker.complete_step("step-1")

        tracker.start_step("step-2")
        tracker.fail_step("step-2")

        tracker.skip_step("step-3")

        tracker.fail_run()

        self.assertIs(tracker.run_status, RunStatus.FAILED)
        self.assertEqual(
            dict(tracker.step_states),
            {
                "step-1": StepStatus.SUCCESS,
                "step-2": StepStatus.FAILED,
                "step-3": StepStatus.SKIPPED,
            },
        )
        self.assertIsNone(tracker.current_step)
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


if __name__ == "__main__":
    unittest.main()
