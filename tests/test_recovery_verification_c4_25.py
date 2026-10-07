import unittest

from application.recovery_execution import RecoveryExecution, RecoveryExecutionResult
from application.recovery_verification import (
    RecoveryVerification,
    RecoveryVerificationService,
)


class TestRecoveryVerificationC425(unittest.TestCase):
    def test_successful_immediate_recovery_requires_real_state(self):
        result = RecoveryExecutionResult(
            outcome=RecoveryExecution.IMMEDIATE_RECOVERY,
            executed=True,
            succeeded=True,
        )
        verification = RecoveryVerificationService(
            state_reader=lambda: "RUNNING"
        ).verify(result, expected_state="RUNNING")

        self.assertEqual(verification.status, RecoveryVerification.VERIFIED)
        self.assertTrue(verification.verified)

    def test_wrong_real_state_is_not_verified(self):
        result = RecoveryExecutionResult(
            outcome=RecoveryExecution.IMMEDIATE_RECOVERY,
            executed=True,
            succeeded=True,
        )
        verification = RecoveryVerificationService(
            state_reader=lambda: "FAILED"
        ).verify(result, expected_state="RUNNING")

        self.assertEqual(verification.status, RecoveryVerification.NOT_VERIFIED)
        self.assertFalse(verification.verified)

    def test_execution_failure_is_not_verified(self):
        result = RecoveryExecutionResult(
            outcome=RecoveryExecution.FAILED,
            executed=True,
            succeeded=False,
            message="recovery failed",
        )
        verification = RecoveryVerificationService(
            state_reader=lambda: "RUNNING"
        ).verify(result, expected_state="RUNNING")

        self.assertEqual(verification.status, RecoveryVerification.NOT_VERIFIED)
        self.assertFalse(verification.verified)

    def test_waiting_state_is_not_verified_as_recovery(self):
        result = RecoveryExecutionResult(
            outcome=RecoveryExecution.WAITING_EXTERNAL,
            executed=False,
            succeeded=False,
        )
        verification = RecoveryVerificationService(
            state_reader=lambda: "WAITING_EXTERNAL"
        ).verify(result, expected_state="RUNNING")

        self.assertEqual(verification.status, RecoveryVerification.WAITING)
        self.assertFalse(verification.verified)

    def test_stop_is_not_verified(self):
        result = RecoveryExecutionResult(
            outcome=RecoveryExecution.STOP,
            executed=False,
            succeeded=False,
        )
        verification = RecoveryVerificationService(
            state_reader=lambda: "STOPPED"
        ).verify(result, expected_state="RUNNING")

        self.assertEqual(verification.status, RecoveryVerification.NOT_VERIFIED)
        self.assertFalse(verification.verified)

    def test_invalid_execution_result_rejected(self):
        with self.assertRaises(TypeError):
            RecoveryVerificationService(
                state_reader=lambda: "RUNNING"
            ).verify("invalid", expected_state="RUNNING")

    def test_missing_state_reader_rejected_for_immediate_recovery(self):
        result = RecoveryExecutionResult(
            outcome=RecoveryExecution.IMMEDIATE_RECOVERY,
            executed=True,
            succeeded=True,
        )
        verification = RecoveryVerificationService().verify(
            result,
            expected_state="RUNNING",
        )

        self.assertEqual(verification.status, RecoveryVerification.NOT_VERIFIED)
        self.assertFalse(verification.verified)


if __name__ == "__main__":
    unittest.main()
