import unittest

from application.emergency_classification import EmergencyClassification
from application.emergency_detector import EmergencyDetection
from application.emergency_snapshot import EmergencySnapshot
from application.observation_event import ObservationEvent


class TestEmergencySnapshotC420(unittest.TestCase):
    def make_classification(self):
        event = ObservationEvent.create(
            event_type="process",
            source="process",
            observed_state="CRASHED",
            payload={"process_id": 1234},
            project_id="project-1",
            task_id="task-1",
            workflow_id="workflow-1",
            execution_id="run-1",
        )
        detection = EmergencyDetection(
            detected=True,
            reason="process_crashed",
            event=event,
        )
        return event, EmergencyClassification(
            category="process",
            severity="critical",
            recoverability="recovery_candidate",
            impact="execution",
            detection=detection,
        )

    def test_snapshot_captures_emergency_classification(self):
        event, classification = self.make_classification()

        snapshot = EmergencySnapshot.create(classification)

        self.assertEqual(snapshot.category, "process")
        self.assertEqual(snapshot.severity, "critical")
        self.assertEqual(snapshot.recoverability, "recovery_candidate")
        self.assertEqual(snapshot.impact, "execution")
        self.assertEqual(snapshot.event.event_id, event.event_id)

    def test_snapshot_preserves_event_context(self):
        event, classification = self.make_classification()

        snapshot = EmergencySnapshot.create(classification)

        self.assertEqual(snapshot.project_id, "project-1")
        self.assertEqual(snapshot.task_id, "task-1")
        self.assertEqual(snapshot.workflow_id, "workflow-1")
        self.assertEqual(snapshot.execution_id, "run-1")

    def test_snapshot_preserves_payload_without_mutating_event(self):
        event, classification = self.make_classification()

        snapshot = EmergencySnapshot.create(classification)

        self.assertEqual(snapshot.event.payload["process_id"], 1234)
        self.assertEqual(event.payload["process_id"], 1234)
        self.assertIsNot(snapshot.event.payload, event.payload)

    def test_invalid_classification_is_rejected(self):
        with self.assertRaises(TypeError):
            EmergencySnapshot.create(object())

    def test_snapshot_is_immutable(self):
        _, classification = self.make_classification()
        snapshot = EmergencySnapshot.create(classification)

        with self.assertRaises(AttributeError):
            snapshot.category = "terminal"


if __name__ == "__main__":
    unittest.main()
