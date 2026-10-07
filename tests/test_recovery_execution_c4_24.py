import unittest

from application.recovery_decision import RecoveryDecision
from application.recovery_execution import (
    RecoveryExecution,
    RecoveryExecutionService,
)


class TestRecoveryExecutionC424(unittest.TestCase):
    def test_waiting_external_does_not_execute(self):
        calls = []
        result = RecoveryExecutionService(
            immediate_recovery=lambda: calls.append("recover")
        ).execute(RecoveryDecision.WAITING_EXTERNAL)

        self.assertEqual(result.outcome, RecoveryExecution.WAITING_EXTERNAL)
        self.assertFalse(result.executed)
        self.assertEqual(calls, [])

    def test_waiting_user_does_not_execute(self):
        calls = []
        result = RecoveryExecutionService(
            immediate_recovery=lambda: calls.append("recover")
        ).execute(RecoveryDecision.WAITING_FOR_USER)

        self.assertEqual(result.outcome, RecoveryExecution.WAITING_FOR_USER)
        self.assertFalse(result.executed)
        self.assertEqual(calls, [])

    def test_stop_does_not_execute(self):
        calls = []
        result = RecoveryExecutionService(
            immediate_recovery=lambda: calls.append("recover")
        ).execute(RecoveryDecision.STOP)

        self.assertEqual(result.outcome, RecoveryExecution.STOP)
        self.assertFalse(result.executed)
        self.assertEqual(calls, [])

    def test_immediate_recovery_executes_real_action(self):
        calls = []
        result = RecoveryExecutionService(
            immediate_recovery=lambda: calls.append("recover")
        ).execute(RecoveryDecision.IMMEDIATE_RECOVERY)

        self.assertEqual(result.outcome, RecoveryExecution.IMMEDIATE_RECOVERY)
        self.assertTrue(result.executed)
        self.assertTrue(result.succeeded)
        self.assertEqual(calls, ["recover"])

    def test_failed_recovery_is_not_reported_as_success(self):
        def fail():
            raise RuntimeError("recovery failed")

        result = RecoveryExecutionService(
            immediate_recovery=fail
        ).execute(RecoveryDecision.IMMEDIATE_RECOVERY)

        self.assertTrue(result.executed)
        self.assertFalse(result.succeeded)
        self.assertEqual(result.outcome, RecoveryExecution.FAILED)
        self.assertIn("recovery failed", result.message)

    def test_invalid_decision_rejected(self):
        with self.assertRaises(TypeError):
            RecoveryExecutionService().execute("IMMEDIATE_RECOVERY")


if __name__ == "__main__":
    unittest.main()
