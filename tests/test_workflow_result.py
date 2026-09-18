import unittest

from agent_workflow.workflow_core import WorkflowStatus, WorkflowStepResult
from agent_workflow.workflow_result import WorkflowResult


class WorkflowResultTests(unittest.TestCase):
    def result(
        self,
        operation: str,
        status: WorkflowStatus,
        result: str,
        success: bool,
    ) -> WorkflowStepResult:
        return WorkflowStepResult(operation, status, result, success)

    def test_empty_results_are_deterministic(self) -> None:
        observation = WorkflowResult.from_step_results(())

        self.assertEqual(observation.step_results, ())
        self.assertEqual(observation.status, WorkflowStatus.RECEIVED)
        self.assertEqual(observation.total_steps, 0)
        self.assertEqual(observation.successful_steps, 0)
        self.assertEqual(observation.failed_steps, 0)
        self.assertEqual(observation.blocked_steps, 0)
        self.assertFalse(observation.completed_successfully)
        self.assertIsNone(observation.failure_index)

    def test_all_successful_steps_complete_successfully(self) -> None:
        results = (
            self.result("first", WorkflowStatus.COMPLETED, "one", True),
            self.result("second", WorkflowStatus.COMPLETED, "two", True),
        )

        observation = WorkflowResult.from_step_results(results)

        self.assertEqual(observation.status, WorkflowStatus.COMPLETED)
        self.assertEqual(observation.total_steps, 2)
        self.assertEqual(observation.successful_steps, 2)
        self.assertEqual(observation.failed_steps, 0)
        self.assertEqual(observation.blocked_steps, 0)
        self.assertTrue(observation.completed_successfully)
        self.assertIsNone(observation.failure_index)
        self.assertIsNone(observation.failed_step)

    def test_failed_step_is_observed(self) -> None:
        results = (
            self.result("first", WorkflowStatus.COMPLETED, "ok", True),
            self.result("second", WorkflowStatus.FAILED, "RuntimeError", False),
        )

        observation = WorkflowResult.from_step_results(results)

        self.assertEqual(observation.status, WorkflowStatus.FAILED)
        self.assertEqual(observation.successful_steps, 1)
        self.assertEqual(observation.failed_steps, 1)
        self.assertEqual(observation.blocked_steps, 0)
        self.assertFalse(observation.completed_successfully)
        self.assertEqual(observation.failure_index, 1)
        self.assertEqual(observation.failed_step, results[1])

    def test_blocked_step_is_observed(self) -> None:
        results = (
            self.result("dangerous", WorkflowStatus.BLOCKED, "DENIED", False),
        )

        observation = WorkflowResult.from_step_results(results)

        self.assertEqual(observation.status, WorkflowStatus.BLOCKED)
        self.assertEqual(observation.total_steps, 1)
        self.assertEqual(observation.successful_steps, 0)
        self.assertEqual(observation.failed_steps, 0)
        self.assertEqual(observation.blocked_steps, 1)
        self.assertFalse(observation.completed_successfully)
        self.assertEqual(observation.failure_index, 0)

    def test_mixed_results_preserve_order_and_counts(self) -> None:
        results = (
            self.result("first", WorkflowStatus.COMPLETED, "ok", True),
            self.result("second", WorkflowStatus.COMPLETED, "ok", True),
            self.result("third", WorkflowStatus.FAILED, "error", False),
            self.result("fourth", WorkflowStatus.BLOCKED, "DENIED", False),
        )

        observation = WorkflowResult.from_step_results(results)

        self.assertEqual(observation.step_results, results)
        self.assertEqual(observation.total_steps, 4)
        self.assertEqual(observation.successful_steps, 2)
        self.assertEqual(observation.failed_steps, 1)
        self.assertEqual(observation.blocked_steps, 1)
        self.assertEqual(observation.failure_index, 2)

    def test_first_unsuccessful_step_is_failure_location(self) -> None:
        results = (
            self.result("first", WorkflowStatus.BLOCKED, "BLOCKED", False),
            self.result("later", WorkflowStatus.FAILED, "error", False),
        )

        observation = WorkflowResult.from_step_results(results)

        self.assertEqual(observation.failure_index, 0)
        self.assertEqual(observation.failed_step, results[0])

    def test_invalid_step_result_type_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            WorkflowResult.from_step_results(
                ("not a workflow result",),  # type: ignore[arg-type]
            )

    def test_result_is_immutable(self) -> None:
        observation = WorkflowResult.from_step_results(
            (
                self.result("first", WorkflowStatus.COMPLETED, "ok", True),
            )
        )

        with self.assertRaises(AttributeError):
            observation.status = WorkflowStatus.FAILED  # type: ignore[misc]

    def test_summary_is_deterministic(self) -> None:
        results = (
            self.result("first", WorkflowStatus.COMPLETED, "ok", True),
            self.result("second", WorkflowStatus.BLOCKED, "DENIED", False),
        )

        observation = WorkflowResult.from_step_results(results)

        self.assertEqual(
            observation.summary(),
            "\n".join(
                [
                    "WORKFLOW RESULT",
                    "Status: BLOCKED",
                    "Total steps: 2",
                    "Successful steps: 1",
                    "Failed steps: 0",
                    "Blocked steps: 1",
                    "Completed successfully: False",
                    "Failure step: 2",
                ]
            ),
        )

    def test_observation_does_not_execute_any_action(self) -> None:
        executed = []

        results = (
            self.result("observation only", WorkflowStatus.COMPLETED, "ready", True),
        )

        observation = WorkflowResult.from_step_results(results)

        executed.append(False)

        self.assertTrue(observation.completed_successfully)
        self.assertEqual(executed, [False])


if __name__ == "__main__":
    unittest.main()
