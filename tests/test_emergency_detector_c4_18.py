import unittest

from application.emergency_detector import EmergencyDetector
from application.observation_event import ObservationEvent


class EmergencyDetectorC418Tests(unittest.TestCase):
    def setUp(self):
        self.detector = EmergencyDetector()

    def event(self, source, state, event_type=None, payload=None):
        return ObservationEvent.create(
            source=source,
            event_type=event_type or source,
            observed_state=state,
            payload=payload or {},
        )

    def test_process_crashed_detected(self):
        event = self.event("process", "CRASHED")
        result = self.detector.detect(event)
        self.assertTrue(result.detected)
        self.assertEqual(result.reason, "process_crashed")
        self.assertIs(result.event, event)

    def test_process_hung_and_failed_detected(self):
        self.assertTrue(self.detector.detect(self.event("process", "HUNG")).detected)
        self.assertTrue(self.detector.detect(self.event("process", "FAILED")).detected)

    def test_terminal_failure_states_detected(self):
        self.assertTrue(self.detector.detect(self.event("terminal", "FAILED")).detected)
        self.assertTrue(
            self.detector.detect(self.event("terminal", "DISCONNECTED")).detected
        )

    def test_external_agent_failure_and_wait_detected(self):
        self.assertTrue(
            self.detector.detect(
                self.event("external_agent", "FAILED")
            ).detected
        )
        self.assertTrue(
            self.detector.detect(
                self.event("external_agent", "waiting_external")
            ).detected
        )

    def test_execution_failure_detected(self):
        result = self.detector.detect(self.event("execution", "FAILED"))
        self.assertTrue(result.detected)
        self.assertEqual(result.reason, "execution_failed")

    def test_vscode_error_detected(self):
        result = self.detector.detect(
            self.event("vscode", "ERROR", event_type="error")
        )
        self.assertTrue(result.detected)
        self.assertEqual(result.reason, "vscode_error")

    def test_normal_events_not_detected(self):
        for source, state in (
            ("process", "RUNNING"),
            ("terminal", "OUTPUT"),
            ("external_agent", "CONNECTED"),
            ("execution", "COMPLETED"),
            ("vscode", "workspace"),
        ):
            result = self.detector.detect(self.event(source, state))
            self.assertFalse(result.detected)
            self.assertIsNone(result.reason)
            self.assertIsNone(result.event)

    def test_invalid_event_rejected(self):
        with self.assertRaises(TypeError):
            self.detector.detect(object())


if __name__ == "__main__":
    unittest.main()
