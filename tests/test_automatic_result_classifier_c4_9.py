import unittest

from agent_workflow.workflow_core import WorkflowStatus
from agent_workflow.workflow_result import WorkflowResult
from application.automatic_result_classifier import (
    AutomaticResultClassifier,
    ResultClassification,
    ResultClassificationEvidence,
)
from permissions.reporting import ApprovalStatus


def result(status):
    return WorkflowResult(
        run_id="run-1",
        status=status,
        step_results=(),
        total_steps=0,
        successful_steps=0,
        failed_steps=0,
        blocked_steps=0,
        completed_successfully=status is WorkflowStatus.COMPLETED,
        failure_index=None,
    )


class AutomaticResultClassifierC49Tests(unittest.TestCase):
    def test_completed_is_success(self):
        self.assertEqual(
            AutomaticResultClassifier.classify(
                result(WorkflowStatus.COMPLETED)
            ),
            ResultClassification.SUCCESS,
        )

    def test_failed_is_failed(self):
        self.assertEqual(
            AutomaticResultClassifier.classify(
                result(WorkflowStatus.FAILED)
            ),
            ResultClassification.FAILED,
        )

    def test_blocked_is_blocked(self):
        self.assertEqual(
            AutomaticResultClassifier.classify(
                result(WorkflowStatus.BLOCKED)
            ),
            ResultClassification.BLOCKED,
        )

    def test_explicit_denied_is_denied(self):
        self.assertEqual(
            AutomaticResultClassifier.classify(
                result(WorkflowStatus.BLOCKED),
                ResultClassificationEvidence(
                    approval_statuses=(ApprovalStatus.DENIED,)
                ),
            ),
            ResultClassification.DENIED,
        )

    def test_invalid_result_is_rejected(self):
        with self.assertRaises(TypeError):
            AutomaticResultClassifier.classify(object())


if __name__ == "__main__":
    unittest.main()
