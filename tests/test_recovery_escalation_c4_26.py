import unittest

from application.recovery_execution import RecoveryExecution, RecoveryExecutionResult
from application.recovery_verification import (
    RecoveryVerification,
    RecoveryVerificationResult,
)
from application.recovery_escalation import (
    RecoveryEscalation,
    RecoveryEscalationService,
)


class TestRecoveryEscalationC426(unittest.TestCase):
    def make_result(self, status):
        return RecoveryVerificationResult(
            status=status,
            verified=status is RecoveryVerification.VERIFIED,
            actual_state="RUNNING" if status is RecoveryVerification.VERIFIED else None,
            expected_state="RUNNING",
        )

    def test_verified_completes(self):
        result = RecoveryEscalationService().decide(
            self.make_result(RecoveryVerification.VERIFIED),
            attempt=1,
        )
        self.assertEqual(result.outcome, RecoveryEscalation.COMPLETED)

    def test_waiting_remains_waiting(self):
        result = RecoveryEscalationService().decide(
            self.make_result(RecoveryVerification.WAITING),
            attempt=1,
        )
        self.assertEqual(result.outcome, RecoveryEscalation.WAITING)

    def test_failed_verification_escalates(self):
        result = RecoveryEscalationService(max_attempts=2).decide(
            self.make_result(RecoveryVerification.NOT_VERIFIED),
            attempt=1,
        )
        self.assertEqual(result.outcome, RecoveryEscalation.ESCALATE)

    def test_attempt_limit_stops(self):
        result = RecoveryEscalationService(max_attempts=2).decide(
            self.make_result(RecoveryVerification.NOT_VERIFIED),
            attempt=2,
        )
        self.assertEqual(result.outcome, RecoveryEscalation.STOP)

    def test_no_unbounded_retry(self):
        result = RecoveryEscalationService(max_attempts=1).decide(
            self.make_result(RecoveryVerification.NOT_VERIFIED),
            attempt=99,
        )
        self.assertEqual(result.outcome, RecoveryEscalation.STOP)

    def test_invalid_verification_rejected(self):
        with self.assertRaises(TypeError):
            RecoveryEscalationService().decide("invalid", attempt=0)

    def test_invalid_attempt_rejected(self):
        verification = self.make_result(RecoveryVerification.NOT_VERIFIED)
        with self.assertRaises(ValueError):
            RecoveryEscalationService().decide(verification, attempt=-1)

    def test_invalid_max_attempts_rejected(self):
        with self.assertRaises(ValueError):
            RecoveryEscalationService(max_attempts=0)


if __name__ == "__main__":
    unittest.main()
