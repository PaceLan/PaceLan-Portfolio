import unittest

from application.observation_event import ObservationEvent
from application.process_lifecycle import ProcessLifecycleState, ProcessSnapshot
from application.process_observation import ProcessObservation


class ProcessObservationC413Tests(unittest.TestCase):
    def test_running_snapshot_becomes_process_event(self):
        snapshot = ProcessSnapshot(
            process_id=101,
            state=ProcessLifecycleState.RUNNING,
        )
        event = ProcessObservation.from_snapshot(snapshot)

        self.assertIsInstance(event, ObservationEvent)
        self.assertEqual(event.event_type, "process")
        self.assertEqual(event.source, "process")
        self.assertEqual(event.observed_state, "RUNNING")
        self.assertEqual(event.payload["process_id"], 101)

    def test_exited_snapshot_preserves_exit_code(self):
        snapshot = ProcessSnapshot(
            process_id=102,
            state=ProcessLifecycleState.EXITED,
            exit_code=0,
        )
        event = ProcessObservation.exited(snapshot)

        self.assertEqual(event.observed_state, "EXITED")
        self.assertEqual(event.payload["exit_code"], 0)

    def test_crashed_snapshot_is_explicit(self):
        snapshot = ProcessSnapshot(
            process_id=103,
            state=ProcessLifecycleState.CRASHED,
            exit_code=1,
        )
        event = ProcessObservation.crashed(snapshot)

        self.assertEqual(event.observed_state, "CRASHED")
        self.assertEqual(event.payload["exit_code"], 1)

    def test_hung_snapshot_is_explicit(self):
        snapshot = ProcessSnapshot(
            process_id=104,
            state=ProcessLifecycleState.HUNG,
        )
        event = ProcessObservation.hung(snapshot)

        self.assertEqual(event.observed_state, "HUNG")

    def test_state_specific_observer_rejects_wrong_state(self):
        snapshot = ProcessSnapshot(
            process_id=105,
            state=ProcessLifecycleState.RUNNING,
        )

        with self.assertRaises(ValueError):
            ProcessObservation.exited(snapshot)

    def test_context_and_custom_payload_are_preserved(self):
        snapshot = ProcessSnapshot(
            process_id=106,
            state=ProcessLifecycleState.RUNNING,
        )
        event = ProcessObservation.from_snapshot(
            snapshot,
            project_id="project-1",
            task_id="task-1",
            workflow_id="workflow-1",
            execution_id="execution-1",
            correlation_id="corr-1",
            payload={"source_detail": "worker"},
        )

        self.assertEqual(event.project_id, "project-1")
        self.assertEqual(event.task_id, "task-1")
        self.assertEqual(event.workflow_id, "workflow-1")
        self.assertEqual(event.execution_id, "execution-1")
        self.assertEqual(event.correlation_id, "corr-1")
        self.assertEqual(event.payload["source_detail"], "worker")

    def test_invalid_snapshot_is_rejected(self):
        with self.assertRaises(TypeError):
            ProcessObservation.from_snapshot("not-a-snapshot")


if __name__ == "__main__":
    unittest.main()
