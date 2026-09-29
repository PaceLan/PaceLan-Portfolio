"""M18.5.5 Application error/result propagation boundary tests."""

import unittest

from agent_workflow.core_interfaces import Result
from agent_workflow.workflow_core import (
    WorkflowStatus,
    WorkflowStepResult,
)
from agent_workflow.workflow_result import WorkflowResult

from application.models import ResultModel
from application.services import ResultService


class ApplicationErrorResultPropagationM1855Tests(unittest.TestCase):
    """Verify Core failures propagate faithfully through Application."""

    # ------------------------------------------------------------------
    # Core Result -> Application ResultModel
    # ------------------------------------------------------------------

    def test_core_failed_result_status_is_propagated(self):
        core = Result(
            run_id="run-001",
            status="FAILED",
        )

        model = ResultService.from_core(core)

        self.assertIsInstance(model, ResultModel)
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.status, "FAILED")

    def test_core_in_progress_result_status_is_propagated(self):
        core = Result(
            run_id="run-002",
            status="IN_PROGRESS",
        )

        model = ResultService.from_core(core)

        self.assertEqual(model.run_id, "run-002")
        self.assertEqual(model.status, "IN_PROGRESS")

    # ------------------------------------------------------------------
    # WorkflowResult failure propagation
    # ------------------------------------------------------------------

    def test_workflow_failure_status_is_propagated(self):
        failed = WorkflowStepResult(
            operation="modify",
            status=WorkflowStatus.FAILED,
            result="failure",
            success=False,
        )

        workflow_result = WorkflowResult.from_step_results(
            (failed,),
            run_id="run-failed-001",
        )

        model = ResultService.from_workflow_result(
            workflow_result,
        )

        self.assertIsInstance(model, ResultModel)
        self.assertEqual(model.run_id, "run-failed-001")
        self.assertEqual(model.status, "FAILED")
        self.assertEqual(model.total_steps, 1)
        self.assertEqual(model.successful_steps, 0)
        self.assertEqual(model.failed_steps, 1)
        self.assertEqual(model.blocked_steps, 0)
        self.assertFalse(model.completed_successfully)
        self.assertEqual(model.failure_index, 0)

    def test_partial_failure_statistics_are_preserved(self):
        successful = WorkflowStepResult(
            operation="inspect",
            status=WorkflowStatus.COMPLETED,
            result="ok",
            success=True,
        )

        failed = WorkflowStepResult(
            operation="modify",
            status=WorkflowStatus.FAILED,
            result="failure",
            success=False,
        )

        workflow_result = WorkflowResult.from_step_results(
            (successful, failed),
            run_id="run-failed-002",
        )

        model = ResultService.from_workflow_result(
            workflow_result,
        )

        self.assertEqual(model.total_steps, 2)
        self.assertEqual(model.successful_steps, 1)
        self.assertEqual(model.failed_steps, 1)
        self.assertEqual(model.blocked_steps, 0)
        self.assertFalse(model.completed_successfully)
        self.assertEqual(model.failure_index, 1)

    # ------------------------------------------------------------------
    # No false success
    # ------------------------------------------------------------------

    def test_failed_workflow_cannot_become_application_success(self):
        failed = WorkflowStepResult(
            operation="write",
            status=WorkflowStatus.FAILED,
            result="failure",
            success=False,
        )

        workflow_result = WorkflowResult.from_step_results(
            (failed,),
            run_id="run-failed-003",
        )

        model = ResultService.from_workflow_result(
            workflow_result,
        )

        self.assertEqual(model.status, "FAILED")
        self.assertFalse(model.completed_successfully)
        self.assertNotEqual(model.status, "COMPLETED")

    # ------------------------------------------------------------------
    # Object isolation
    # ------------------------------------------------------------------

    def test_failure_propagation_returns_application_model(self):
        failed = WorkflowStepResult(
            operation="write",
            status=WorkflowStatus.FAILED,
            result="failure",
            success=False,
        )

        workflow_result = WorkflowResult.from_step_results(
            (failed,),
            run_id="run-isolation-001",
        )

        model = ResultService.from_workflow_result(
            workflow_result,
        )

        self.assertIsInstance(model, ResultModel)
        self.assertIsNot(model, workflow_result)

    def test_application_result_contains_no_core_result_object(self):
        failed = WorkflowStepResult(
            operation="write",
            status=WorkflowStatus.FAILED,
            result="failure",
            success=False,
        )

        workflow_result = WorkflowResult.from_step_results(
            (failed,),
            run_id="run-isolation-002",
        )

        model = ResultService.from_workflow_result(
            workflow_result,
        )

        for value in (
            model.run_id,
            model.status,
            model.total_steps,
            model.successful_steps,
            model.failed_steps,
            model.blocked_steps,
            model.completed_successfully,
            model.failure_index,
        ):
            self.assertNotIsInstance(value, WorkflowResult)
            self.assertNotIsInstance(value, Result)

    # ------------------------------------------------------------------
    # Invalid inputs
    # ------------------------------------------------------------------

    def test_invalid_core_result_is_rejected(self):
        with self.assertRaises(TypeError):
            ResultService.from_core(object())

    def test_invalid_workflow_result_is_rejected(self):
        with self.assertRaises(TypeError):
            ResultService.from_workflow_result(object())

    # ------------------------------------------------------------------
    # Result mapping is deterministic
    # ------------------------------------------------------------------

    def test_same_core_failure_produces_equivalent_application_models(self):
        failed = WorkflowStepResult(
            operation="write",
            status=WorkflowStatus.FAILED,
            result="failure",
            success=False,
        )

        first_core = WorkflowResult.from_step_results(
            (failed,),
            run_id="run-deterministic-001",
        )

        second_core = WorkflowResult.from_step_results(
            (failed,),
            run_id="run-deterministic-001",
        )

        first_model = ResultService.from_workflow_result(
            first_core,
        )
        second_model = ResultService.from_workflow_result(
            second_core,
        )

        self.assertEqual(first_model, second_model)
        self.assertIsNot(first_model, second_model)


if __name__ == "__main__":
    unittest.main()