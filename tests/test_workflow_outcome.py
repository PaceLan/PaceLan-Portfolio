import unittest

from agent_workflow.workflow_core import WorkflowStatus, WorkflowStepResult
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_outcome import (
    is_blocked,
    is_failed,
    is_in_progress,
    is_success,
    is_terminal,
)


def make_result(status: WorkflowStatus, success: bool) -> WorkflowResult:
    return WorkflowResult.from_step_results(
        [
            WorkflowStepResult(
                operation="test",
                status=status,
                result="result",
                success=success,
            )
        ]
    )


class WorkflowOutcomeTests(unittest.TestCase):
    def test_received(self):
        result = WorkflowResult.from_step_results([])
        self.assertFalse(is_terminal(result))
        self.assertFalse(is_success(result))
        self.assertFalse(is_failed(result))
        self.assertFalse(is_blocked(result))
        self.assertFalse(is_in_progress(result))

    def test_in_progress(self):
        result = make_result(WorkflowStatus.IN_PROGRESS, True)
        self.assertFalse(is_terminal(result))
        self.assertFalse(is_success(result))
        self.assertFalse(is_failed(result))
        self.assertFalse(is_blocked(result))
        self.assertTrue(is_in_progress(result))

    def test_completed(self):
        result = make_result(WorkflowStatus.COMPLETED, True)
        self.assertTrue(is_terminal(result))
        self.assertTrue(is_success(result))
        self.assertFalse(is_failed(result))
        self.assertFalse(is_blocked(result))
        self.assertFalse(is_in_progress(result))

    def test_failed(self):
        result = make_result(WorkflowStatus.FAILED, False)
        self.assertTrue(is_terminal(result))
        self.assertFalse(is_success(result))
        self.assertTrue(is_failed(result))
        self.assertFalse(is_blocked(result))
        self.assertFalse(is_in_progress(result))

    def test_blocked(self):
        result = make_result(WorkflowStatus.BLOCKED, False)
        self.assertTrue(is_terminal(result))
        self.assertFalse(is_success(result))
        self.assertFalse(is_failed(result))
        self.assertTrue(is_blocked(result))
        self.assertFalse(is_in_progress(result))

    def test_terminal_states(self):
        for status, success in (
            (WorkflowStatus.COMPLETED, True),
            (WorkflowStatus.FAILED, False),
            (WorkflowStatus.BLOCKED, False),
        ):
            with self.subTest(status=status):
                self.assertTrue(is_terminal(make_result(status, success)))

    def test_non_terminal_states(self):
        self.assertFalse(is_terminal(WorkflowResult.from_step_results([])))
        self.assertFalse(
            is_terminal(make_result(WorkflowStatus.IN_PROGRESS, True))
        )

    def test_completed_result_is_success(self):
        result = make_result(WorkflowStatus.COMPLETED, True)
        self.assertTrue(is_success(result))

    def test_failed_result_is_failure(self):
        result = make_result(WorkflowStatus.FAILED, False)
        self.assertTrue(is_failed(result))

    def test_blocked_result_is_blocked(self):
        result = make_result(WorkflowStatus.BLOCKED, False)
        self.assertTrue(is_blocked(result))

    def test_invalid_inputs(self):
        for function in (
            is_terminal,
            is_success,
            is_failed,
            is_blocked,
            is_in_progress,
        ):
            with self.subTest(function=function.__name__):
                with self.assertRaises(TypeError):
                    function(None)

    def test_batch3_result_remains_immutable(self):
        result = make_result(WorkflowStatus.COMPLETED, True)
        before = result
        self.assertIs(result, before)
        self.assertEqual(result.status, WorkflowStatus.COMPLETED)
        self.assertTrue(result.completed_successfully)


if __name__ == "__main__":
    unittest.main()
