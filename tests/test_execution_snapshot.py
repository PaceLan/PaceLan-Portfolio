import unittest
from datetime import datetime, timezone
from types import MappingProxyType

from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_tracker import RunStatus, StepStatus


class ExecutionSnapshotTests(unittest.TestCase):

    def make_snapshot(self):
        started_at = datetime.now(timezone.utc)
        finished_at = datetime.now(timezone.utc)

        return ExecutionSnapshot(
            run_id="run-1",
            task_id="task-1",
            run_status=RunStatus.RUNNING,
            step_states={
                "step-1": StepStatus.RUNNING,
                "step-2": StepStatus.PENDING,
            },
            current_step="step-1",
            started_at=started_at,
            finished_at=finished_at,
        )

    def test_fields_are_preserved(self):
        snapshot = self.make_snapshot()

        self.assertEqual(snapshot.run_id, "run-1")
        self.assertEqual(snapshot.task_id, "task-1")
        self.assertIs(snapshot.run_status, RunStatus.RUNNING)
        self.assertEqual(snapshot.current_step, "step-1")
        self.assertIsNotNone(snapshot.started_at)
        self.assertIsNotNone(snapshot.finished_at)

    def test_step_states_are_mapping_proxy(self):
        snapshot = self.make_snapshot()

        self.assertIsInstance(
            snapshot.step_states,
            MappingProxyType,
        )

    def test_step_states_are_read_only(self):
        snapshot = self.make_snapshot()

        with self.assertRaises(TypeError):
            snapshot.step_states["step-1"] = StepStatus.SUCCESS

    def test_step_states_are_copied(self):
        states = {
            "step-1": StepStatus.RUNNING,
            "step-2": StepStatus.PENDING,
        }

        snapshot = ExecutionSnapshot(
            run_id="run-1",
            task_id="task-1",
            run_status=RunStatus.RUNNING,
            step_states=states,
            current_step="step-1",
            started_at=None,
            finished_at=None,
        )

        states["step-1"] = StepStatus.SUCCESS
        states["step-2"] = StepStatus.SKIPPED

        self.assertIs(
            snapshot.step_states["step-1"],
            StepStatus.RUNNING,
        )
        self.assertIs(
            snapshot.step_states["step-2"],
            StepStatus.PENDING,
        )

    def test_top_level_fields_are_immutable(self):
        snapshot = self.make_snapshot()

        with self.assertRaises(AttributeError):
            snapshot.run_id = "run-2"

        with self.assertRaises(AttributeError):
            snapshot.run_status = RunStatus.COMPLETED

        with self.assertRaises(AttributeError):
            snapshot.current_step = "step-2"

    def test_snapshot_is_independent_of_original_mapping(self):
        states = {
            "step-1": StepStatus.PENDING,
        }

        snapshot = ExecutionSnapshot(
            run_id="run-1",
            task_id="task-1",
            run_status=RunStatus.CREATED,
            step_states=states,
            current_step=None,
            started_at=None,
            finished_at=None,
        )

        states.clear()

        self.assertEqual(
            dict(snapshot.step_states),
            {"step-1": StepStatus.PENDING},
        )


if __name__ == "__main__":
    unittest.main()