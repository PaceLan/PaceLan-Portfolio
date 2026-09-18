import unittest

from agent_workflow.workflow_core import WorkflowStatus, WorkflowStepResult
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.result_analysis import WorkflowResultAnalysis


class WorkflowResultAnalysisTests(unittest.TestCase):

    def step(
        self,
        operation: str,
        status: WorkflowStatus,
        result: str,
        success: bool,
    ) -> WorkflowStepResult:
        return WorkflowStepResult(
            operation=operation,
            status=status,
            result=result,
            success=success,
        )

    def test_all_successful(self):
        result = WorkflowResult.from_step_results(
            [
                self.step(
                    "step-1",
                    WorkflowStatus.COMPLETED,
                    "done",
                    True,
                ),
                self.step(
                    "step-2",
                    WorkflowStatus.COMPLETED,
                    "done",
                    True,
                ),
            ]
        )

        analysis = WorkflowResultAnalysis.from_result(result)

        self.assertTrue(analysis.is_successful)
        self.assertFalse(analysis.has_failure)
        self.assertFalse(analysis.has_blocked_step)
        self.assertIsNone(analysis.first_failed_step)
        self.assertEqual(
            ("step-1", "step-2"),
            analysis.successful_operations,
        )
        self.assertEqual((), analysis.failed_operations)
        self.assertEqual((), analysis.blocked_operations)

    def test_failed_result(self):
        failed = self.step(
            "step-2",
            WorkflowStatus.FAILED,
            "failed",
            False,
        )

        result = WorkflowResult.from_step_results(
            [
                self.step(
                    "step-1",
                    WorkflowStatus.COMPLETED,
                    "done",
                    True,
                ),
                failed,
            ]
        )

        analysis = WorkflowResultAnalysis.from_result(result)

        self.assertFalse(analysis.is_successful)
        self.assertTrue(analysis.has_failure)
        self.assertFalse(analysis.has_blocked_step)
        self.assertIs(analysis.first_failed_step, failed)
        self.assertEqual(
            ("step-2",),
            analysis.failed_operations,
        )
        self.assertEqual(
            ("step-1",),
            analysis.successful_operations,
        )

    def test_blocked_result(self):
        blocked = self.step(
            "step-3",
            WorkflowStatus.BLOCKED,
            "blocked",
            False,
        )

        result = WorkflowResult.from_step_results(
            [
                self.step(
                    "step-1",
                    WorkflowStatus.COMPLETED,
                    "done",
                    True,
                ),
                blocked,
            ]
        )

        analysis = WorkflowResultAnalysis.from_result(result)

        self.assertFalse(analysis.is_successful)
        self.assertFalse(analysis.has_failure)
        self.assertTrue(analysis.has_blocked_step)
        self.assertIsNone(analysis.first_failed_step)
        self.assertEqual(
            ("step-3",),
            analysis.blocked_operations,
        )

    def test_multiple_failures_preserve_order(self):
        result = WorkflowResult.from_step_results(
            [
                self.step(
                    "step-1",
                    WorkflowStatus.FAILED,
                    "first failure",
                    False,
                ),
                self.step(
                    "step-2",
                    WorkflowStatus.FAILED,
                    "second failure",
                    False,
                ),
            ]
        )

        analysis = WorkflowResultAnalysis.from_result(result)

        self.assertEqual(
            ("step-1", "step-2"),
            analysis.failed_operations,
        )
        self.assertEqual(
            "step-1",
            analysis.first_failed_step.operation,
        )

    def test_empty_result(self):
        result = WorkflowResult.from_step_results([])

        analysis = WorkflowResultAnalysis.from_result(result)

        self.assertFalse(analysis.is_successful)
        self.assertFalse(analysis.has_failure)
        self.assertFalse(analysis.has_blocked_step)
        self.assertIsNone(analysis.first_failed_step)
        self.assertEqual((), analysis.failed_operations)
        self.assertEqual((), analysis.blocked_operations)
        self.assertEqual((), analysis.successful_operations)

    def test_invalid_input_is_rejected(self):
        with self.assertRaises(TypeError):
            WorkflowResultAnalysis.from_result("not a workflow result")

    def test_analysis_is_immutable(self):
        result = WorkflowResult.from_step_results(
            [
                self.step(
                    "step-1",
                    WorkflowStatus.COMPLETED,
                    "done",
                    True,
                )
            ]
        )

        analysis = WorkflowResultAnalysis.from_result(result)

        with self.assertRaises(AttributeError):
            analysis.is_successful = False


if __name__ == "__main__":
    unittest.main()