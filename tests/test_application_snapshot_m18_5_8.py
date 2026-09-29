import unittest
from datetime import datetime

from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_tracking import RunStatus, StepStatus

from application.models import SnapshotModel
from application.services import SnapshotService


class ApplicationSnapshotM1858Tests(unittest.TestCase):
    def _snapshot(self):
        started_at = datetime(2026, 9, 28, 10, 30, 0)
        finished_at = datetime(2026, 9, 28, 10, 31, 0)

        return ExecutionSnapshot(
            run_id="run-001",
            task_id="task-001",
            run_status=RunStatus.COMPLETED,
            step_states={
                "step-001": StepStatus.SUCCESS,
                "step-002": StepStatus.FAILED,
            },
            current_step="step-002",
            started_at=started_at,
            finished_at=finished_at,
        )

    def test_snapshot_maps_to_application_model(self):
        snapshot = self._snapshot()

        model = SnapshotService.from_core(snapshot)

        self.assertIsInstance(model, SnapshotModel)

    def test_snapshot_identity_fields_are_preserved(self):
        snapshot = self._snapshot()

        model = SnapshotService.from_core(snapshot)

        self.assertEqual(model.run_id, snapshot.run_id)
        self.assertEqual(model.task_id, snapshot.task_id)
        self.assertEqual(model.current_step, snapshot.current_step)
        self.assertEqual(model.started_at, snapshot.started_at)
        self.assertEqual(model.finished_at, snapshot.finished_at)

    def test_run_status_is_mapped_to_stable_string(self):
        snapshot = self._snapshot()

        model = SnapshotService.from_core(snapshot)

        self.assertEqual(
            model.run_status,
            snapshot.run_status.value,
        )
        self.assertIsInstance(model.run_status, str)

    def test_step_states_are_mapped_to_stable_strings(self):
        snapshot = self._snapshot()

        model = SnapshotService.from_core(snapshot)

        self.assertEqual(
            model.step_states["step-001"],
            StepStatus.SUCCESS.value,
        )
        self.assertEqual(
            model.step_states["step-002"],
            StepStatus.FAILED.value,
        )

        for state in model.step_states.values():
            self.assertIsInstance(state, str)

    def test_application_step_states_are_detached_from_core_mapping(self):
        source_states = {
            "step-001": StepStatus.SUCCESS,
        }

        snapshot = ExecutionSnapshot(
            run_id="run-001",
            task_id="task-001",
            run_status=RunStatus.COMPLETED,
            step_states=source_states,
            current_step=None,
            started_at=None,
            finished_at=None,
        )

        model = SnapshotService.from_core(snapshot)

        source_states["step-002"] = StepStatus.FAILED

        self.assertEqual(
            model.step_states,
            {"step-001": StepStatus.SUCCESS.value},
        )
        self.assertNotIn("step-002", model.step_states)

    def test_application_snapshot_is_immutable(self):
        snapshot = self._snapshot()

        model = SnapshotService.from_core(snapshot)

        with self.assertRaises(TypeError):
            model.step_states["step-003"] = "SUCCESS"

    def test_invalid_snapshot_is_rejected(self):
        with self.assertRaises(TypeError):
            SnapshotService.from_core(object())


if __name__ == "__main__":
    unittest.main()
