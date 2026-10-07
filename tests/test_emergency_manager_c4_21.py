import unittest

from application.emergency_classification import EmergencyClassification
from application.emergency_detector import EmergencyDetection
from application.emergency_manager import EmergencyManager
from application.emergency_snapshot import EmergencySnapshot
from application.observation_event import ObservationEvent


class TestEmergencyManagerC421(unittest.TestCase):
    def make_event(self):
        return ObservationEvent.create(
            event_type="process",
            source="process",
            observed_state="CRASHED",
            payload={"process_id": 1234},
            project_id="project-1",
            task_id="task-1",
            execution_id="run-1",
        )

    def test_process_detect_classify_snapshot(self):
        manager = EmergencyManager()
        result = manager.process(self.make_event())

        self.assertIsNotNone(result)
        self.assertIsInstance(result.detection, EmergencyDetection)
        self.assertTrue(result.detection.detected)
        self.assertIsInstance(result.classification, EmergencyClassification)
        self.assertIsInstance(result.snapshot, EmergencySnapshot)
        self.assertEqual(result.classification.category, "process")
        self.assertEqual(result.classification.severity, "critical")

    def test_normal_event_is_not_an_emergency(self):
        manager = EmergencyManager()
        event = ObservationEvent.create(
            event_type="process",
            source="process",
            observed_state="RUNNING",
            payload={},
        )

        result = manager.process(event)

        self.assertIsNotNone(result)
        self.assertFalse(result.detection.detected)
        self.assertIsNone(result.classification)
        self.assertIsNone(result.snapshot)

    def test_manager_does_not_execute_recovery(self):
        manager = EmergencyManager()
        result = manager.process(self.make_event())

        self.assertFalse(result.recovery_started)
        self.assertFalse(result.verification_started)
        self.assertFalse(result.escalation_started)

    def test_invalid_event_is_rejected(self):
        with self.assertRaises(TypeError):
            EmergencyManager().process(object())


if __name__ == "__main__":
    unittest.main()
