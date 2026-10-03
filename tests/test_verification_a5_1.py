import unittest

from agent_workflow.workflow_core import WorkflowStatus, WorkflowStepResult
from agent_workflow.workflow_result import WorkflowResult
from application.verification import (
    VerificationService,
    VerificationStatus,
)


class TestVerificationServiceA5_1(unittest.TestCase):
    def _result(self, *steps):
        return WorkflowResult.from_step_results(
            list(steps),
            run_id="run-a5",
        )

    def test_successful_execution_is_verified(self):
        result = self._result(
            WorkflowStepResult(
                "step-one",
                WorkflowStatus.COMPLETED,
                "ok",
                True,
            )
        )

        verification = VerificationService.verify(result)

        self.assertTrue(verification.verified)
        self.assertEqual(
            verification.status,
            VerificationStatus.VERIFIED,
        )
        self.assertEqual(verification.run_id, "run-a5")

    def test_failed_execution_is_not_verified(self):
        result = self._result(
            WorkflowStepResult(
                "step-one",
                WorkflowStatus.FAILED,
                "failed",
                False,
            )
        )

        verification = VerificationService.verify(result)

        self.assertFalse(verification.verified)
        self.assertEqual(
            verification.status,
            VerificationStatus.NOT_VERIFIED,
        )

    def test_blocked_execution_is_blocked(self):
        result = self._result(
            WorkflowStepResult(
                "step-one",
                WorkflowStatus.BLOCKED,
                "approval required",
                False,
            )
        )

        verification = VerificationService.verify(result)

        self.assertFalse(verification.verified)
        self.assertEqual(
            verification.status,
            VerificationStatus.BLOCKED,
        )

    def test_verification_does_not_mutate_workflow_result(self):
        result = self._result(
            WorkflowStepResult(
                "step-one",
                WorkflowStatus.COMPLETED,
                "ok",
                True,
            )
        )

        VerificationService.verify(result)

        self.assertEqual(
            result.status,
            WorkflowStatus.COMPLETED,
        )
        self.assertTrue(result.completed_successfully)


if __name__ == "__main__":
    unittest.main()
