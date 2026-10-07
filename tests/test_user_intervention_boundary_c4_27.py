import unittest

from application.recovery_escalation import (
    RecoveryEscalation,
    RecoveryEscalationResult,
)
from application.recovery_execution import (
    RecoveryExecution,
    RecoveryExecutionResult,
)
from application.user_intervention_boundary import (
    UserInterventionBoundary,
    UserInterventionRequirement,
)


class TestUserInterventionBoundaryC427(unittest.TestCase):
    def make_execution(self, outcome):
        return RecoveryExecutionResult(
            outcome=outcome,
            executed=outcome is RecoveryExecution.IMMEDIATE_RECOVERY,
            succeeded=outcome is RecoveryExecution.IMMEDIATE_RECOVERY,
        )

    def make_escalation(self, outcome):
        return RecoveryEscalationResult(
            outcome=outcome,
            attempt=1,
            max_attempts=2,
        )

    def test_waiting_for_user_requires_intervention(self):
        result = UserInterventionBoundary().decide(
            self.make_execution(RecoveryExecution.WAITING_FOR_USER),
            self.make_escalation(RecoveryEscalation.WAITING),
        )
        self.assertEqual(
            result.requirement,
            UserInterventionRequirement.REQUIRED,
        )

    def test_failed_execution_requires_intervention(self):
        result = UserInterventionBoundary().decide(
            self.make_execution(RecoveryExecution.FAILED),
            self.make_escalation(RecoveryEscalation.STOP),
        )
        self.assertEqual(
            result.requirement,
            UserInterventionRequirement.REQUIRED,
        )

    def test_stop_requires_intervention(self):
        result = UserInterventionBoundary().decide(
            self.make_execution(RecoveryExecution.STOP),
            self.make_escalation(RecoveryEscalation.STOP),
        )
        self.assertEqual(
            result.requirement,
            UserInterventionRequirement.REQUIRED,
        )

    def test_escalation_requires_intervention(self):
        result = UserInterventionBoundary().decide(
            self.make_execution(RecoveryExecution.IMMEDIATE_RECOVERY),
            self.make_escalation(RecoveryEscalation.ESCALATE),
        )
        self.assertEqual(
            result.requirement,
            UserInterventionRequirement.REQUIRED,
        )

    def test_external_wait_does_not_require_user(self):
        result = UserInterventionBoundary().decide(
            self.make_execution(RecoveryExecution.WAITING_EXTERNAL),
            self.make_escalation(RecoveryEscalation.WAITING),
        )
        self.assertEqual(
            result.requirement,
            UserInterventionRequirement.NOT_REQUIRED,
        )

    def test_completed_does_not_require_user(self):
        result = UserInterventionBoundary().decide(
            self.make_execution(RecoveryExecution.IMMEDIATE_RECOVERY),
            self.make_escalation(RecoveryEscalation.COMPLETED),
        )
        self.assertEqual(
            result.requirement,
            UserInterventionRequirement.NOT_REQUIRED,
        )

    def test_invalid_execution_rejected(self):
        with self.assertRaises(TypeError):
            UserInterventionBoundary().decide(
                "invalid",
                self.make_escalation(RecoveryEscalation.COMPLETED),
            )

    def test_invalid_escalation_rejected(self):
        with self.assertRaises(TypeError):
            UserInterventionBoundary().decide(
                self.make_execution(RecoveryExecution.IMMEDIATE_RECOVERY),
                "invalid",
            )


if __name__ == "__main__":
    unittest.main()
