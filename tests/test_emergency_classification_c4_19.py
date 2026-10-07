from application.emergency_detector import EmergencyDetection
from application.emergency_classification import (
    EmergencyClassification,
    EmergencyClassifier,
)
from application.observation_event import ObservationEvent


def make_detection(source, state, reason, payload=None):
    event = ObservationEvent.create(
        event_type=source,
        source=source,
        observed_state=state,
        payload=payload or {},
    )
    return EmergencyDetection(
        detected=True,
        reason=reason,
        event=event,
    )


class EmergencyClassifierC419Tests:
    pass


import unittest


class TestEmergencyClassifierC419(unittest.TestCase):
    def test_process_crashed_is_critical_process_emergency(self):
        detection = make_detection("process", "CRASHED", "process_crashed")
        result = EmergencyClassifier().classify(detection)

        self.assertIsInstance(result, EmergencyClassification)
        self.assertEqual(result.category, "process")
        self.assertEqual(result.severity, "critical")
        self.assertEqual(result.recoverability, "recovery_candidate")
        self.assertEqual(result.impact, "execution")

    def test_process_hung_is_high_process_emergency(self):
        detection = make_detection("process", "HUNG", "process_hung")
        result = EmergencyClassifier().classify(detection)

        self.assertEqual(result.category, "process")
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.recoverability, "recovery_candidate")
        self.assertEqual(result.impact, "execution")

    def test_terminal_failure_is_high_terminal_emergency(self):
        detection = make_detection("terminal", "FAILED", "terminal_failed")
        result = EmergencyClassifier().classify(detection)

        self.assertEqual(result.category, "terminal")
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.recoverability, "recovery_candidate")
        self.assertEqual(result.impact, "execution")

    def test_external_waiting_is_external_wait_not_failure(self):
        detection = make_detection(
            "external_agent",
            "WAITING_EXTERNAL",
            "external_agent_waiting",
            {"reason": "quota_limit", "recoverable": True},
        )
        result = EmergencyClassifier().classify(detection)

        self.assertEqual(result.category, "external_agent")
        self.assertEqual(result.severity, "medium")
        self.assertEqual(result.recoverability, "waiting_external")
        self.assertEqual(result.impact, "external_dependency")

    def test_external_failure_is_high_external_emergency(self):
        detection = make_detection(
            "external_agent",
            "FAILED",
            "external_agent_failed",
        )
        result = EmergencyClassifier().classify(detection)

        self.assertEqual(result.category, "external_agent")
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.recoverability, "recovery_candidate")
        self.assertEqual(result.impact, "external_dependency")

    def test_execution_failure_is_high_execution_emergency(self):
        detection = make_detection(
            "execution",
            "FAILED",
            "execution_failed",
        )
        result = EmergencyClassifier().classify(detection)

        self.assertEqual(result.category, "execution")
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.recoverability, "recovery_candidate")
        self.assertEqual(result.impact, "execution")

    def test_vscode_error_is_high_vscode_emergency(self):
        detection = make_detection("vscode", "error", "vscode_error")
        result = EmergencyClassifier().classify(detection)

        self.assertEqual(result.category, "vscode")
        self.assertEqual(result.severity, "high")
        self.assertEqual(result.recoverability, "recovery_candidate")
        self.assertEqual(result.impact, "development_environment")

    def test_undetected_event_is_rejected(self):
        event = ObservationEvent.create(
            event_type="process",
            source="process",
            observed_state="RUNNING",
            payload={},
        )
        detection = EmergencyDetection(
            detected=False,
            reason=None,
            event=None,
        )

        with self.assertRaises(ValueError):
            EmergencyClassifier().classify(detection)

    def test_unknown_reason_is_rejected(self):
        detection = make_detection(
            "process",
            "FAILED",
            "unknown_emergency",
        )

        with self.assertRaises(ValueError):
            EmergencyClassifier().classify(detection)


if __name__ == "__main__":
    unittest.main()
