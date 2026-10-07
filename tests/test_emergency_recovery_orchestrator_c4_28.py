import tempfile
import unittest

from application.emergency_recovery_orchestrator import (
    EmergencyRecoveryOrchestrator,
)
from application.observation_event import ObservationEvent
from application.recovery_execution import RecoveryExecutionService
from application.recovery_verification import RecoveryVerificationService
from application.recovery_state_storage import RecoveryStateStorage


class TestEmergencyRecoveryOrchestratorC428(unittest.TestCase):
    def make_event(self, state="CRASHED", payload=None):
        return ObservationEvent.create(
            event_type="process",
            source="process",
            observed_state=state,
            payload=payload or {},
            project_id="project-1",
            task_id="task-1",
        )

    def test_normal_event_does_not_start_recovery(self):
        result = EmergencyRecoveryOrchestrator().recover(
            self.make_event("RUNNING"),
            expected_state="RUNNING",
        )
        self.assertFalse(result.emergency)
        self.assertEqual(result.status, "NO_EMERGENCY")

    def test_waiting_external_is_not_executed(self):
        event = ObservationEvent.create(
            event_type="external_agent",
            source="external_agent",
            observed_state="WAITING_EXTERNAL",
            payload={"reason": "connection_lost"},
            project_id="project-1",
            task_id="task-1",
        )
        result = EmergencyRecoveryOrchestrator().recover(
            event,
            expected_state="RUNNING",
        )
        self.assertEqual(result.status, "WAITING_EXTERNAL")
        self.assertFalse(result.execution.executed)

    def test_waiting_for_user_is_not_executed(self):
        event = ObservationEvent.create(
            event_type="external_agent",
            source="external_agent",
            observed_state="WAITING_EXTERNAL",
            payload={"reason": "safety_check"},
            project_id="project-1",
            task_id="task-1",
        )
        result = EmergencyRecoveryOrchestrator().recover(
            event,
            expected_state="RUNNING",
        )
        self.assertEqual(result.status, "WAITING_FOR_USER")
        self.assertFalse(result.execution.executed)
        self.assertEqual(
            result.intervention.requirement.value,
            "REQUIRED",
        )

    def test_success_requires_real_verification(self):
        observed = []

        def recover():
            observed.append("executed")

        service = RecoveryExecutionService(recover)
        verifier = RecoveryVerificationService(lambda: "RUNNING")

        result = EmergencyRecoveryOrchestrator(
            execution_service=service,
            verification_service=verifier,
        ).recover(
            self.make_event(),
            expected_state="RUNNING",
        )

        self.assertEqual(observed, ["executed"])
        self.assertEqual(result.status, "VERIFIED")
        self.assertTrue(result.verification.verified)

    def test_failed_verification_escalates(self):
        service = RecoveryExecutionService(lambda: None)
        verifier = RecoveryVerificationService(lambda: "FAILED")

        result = EmergencyRecoveryOrchestrator(
            execution_service=service,
            verification_service=verifier,
        ).recover(
            self.make_event(),
            expected_state="RUNNING",
        )

        self.assertEqual(result.status, "ESCALATE")
        self.assertEqual(
            result.intervention.requirement.value,
            "REQUIRED",
        )

    def test_recovery_state_is_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = RecoveryStateStorage(directory)
            service = RecoveryExecutionService(lambda: None)
            verifier = RecoveryVerificationService(lambda: "RUNNING")

            result = EmergencyRecoveryOrchestrator(
                execution_service=service,
                verification_service=verifier,
                state_storage=storage,
            ).recover(
                self.make_event(),
                expected_state="RUNNING",
            )

            state = storage.load()
            self.assertIsNotNone(state)
            self.assertEqual(state.recovery_id, result.recovery_id)
            self.assertEqual(state.status, "VERIFIED")

    def test_execution_failure_cannot_be_reported_successfully(self):
        def fail():
            raise RuntimeError("executor failed")

        result = EmergencyRecoveryOrchestrator(
            execution_service=RecoveryExecutionService(fail),
        ).recover(
            self.make_event(),
            expected_state="RUNNING",
        )

        self.assertNotEqual(result.status, "VERIFIED")
        self.assertFalse(result.verification.verified)
        self.assertEqual(
            result.intervention.requirement.value,
            "REQUIRED",
        )


if __name__ == "__main__":
    unittest.main()
