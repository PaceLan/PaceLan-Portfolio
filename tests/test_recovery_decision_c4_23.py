import unittest

from application.emergency_classification import EmergencyClassification
from application.emergency_detector import EmergencyDetection
from application.emergency_snapshot import EmergencySnapshot
from application.observation_event import ObservationEvent
from application.recovery_decision import (
    RecoveryDecision,
    RecoveryDecisionEngine,
)


class TestRecoveryDecisionC423(unittest.TestCase):
    def event(self, state, payload=None):
        return ObservationEvent.create(
            event_type="external_agent",
            source="external_agent",
            observed_state=state,
            payload=payload or {},
            task_id="task-1",
        )

    def classification(self, event, recoverability):
        detection = EmergencyDetection(
            detected=True,
            reason="external_agent_waiting",
            event=event,
        )
        return EmergencyClassification(
            category="external_agent",
            severity="medium",
            recoverability=recoverability,
            impact="external_dependency",
            detection=detection,
        )

    def test_recoverable_means_immediate_recovery(self):
        event = self.event("RECOVERABLE")
        result = RecoveryDecisionEngine().decide(
            self.classification(event, "recovery_candidate")
        )
        self.assertEqual(result.decision, RecoveryDecision.IMMEDIATE_RECOVERY)

    def test_connection_lost_waits_external(self):
        event = self.event(
            "WAITING_EXTERNAL",
            {"reason": "connection_lost", "recoverable": True},
        )
        result = RecoveryDecisionEngine().decide(
            self.classification(event, "waiting_external")
        )
        self.assertEqual(result.decision, RecoveryDecision.WAITING_EXTERNAL)

    def test_safety_check_waits_user(self):
        event = self.event(
            "WAITING_EXTERNAL",
            {"reason": "safety_check", "recoverable": True},
        )
        result = RecoveryDecisionEngine().decide(
            self.classification(event, "waiting_external")
        )
        self.assertEqual(result.decision, RecoveryDecision.WAITING_FOR_USER)

    def test_quota_limit_waits_external(self):
        event = self.event(
            "WAITING_EXTERNAL",
            {"reason": "quota_limit", "recoverable": True},
        )
        result = RecoveryDecisionEngine().decide(
            self.classification(event, "waiting_external")
        )
        self.assertEqual(result.decision, RecoveryDecision.WAITING_EXTERNAL)

    def test_unknown_waiting_reason_stops(self):
        event = self.event(
            "WAITING_EXTERNAL",
            {"reason": "unknown", "recoverable": True},
        )
        result = RecoveryDecisionEngine().decide(
            self.classification(event, "waiting_external")
        )
        self.assertEqual(result.decision, RecoveryDecision.STOP)

    def test_non_recoverable_stops(self):
        event = self.event("FAILED")
        result = RecoveryDecisionEngine().decide(
            self.classification(event, "unknown")
        )
        self.assertEqual(result.decision, RecoveryDecision.STOP)

    def test_invalid_classification_rejected(self):
        with self.assertRaises(TypeError):
            RecoveryDecisionEngine().decide(object())


if __name__ == "__main__":
    unittest.main()
