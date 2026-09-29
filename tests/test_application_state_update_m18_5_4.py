"""M18.5.4 Application state update boundary tests."""

import unittest
from dataclasses import FrozenInstanceError

from agent_workflow.core_interfaces import (
    Execution,
    Result,
    Run,
)
from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.workflow_core import (
    WorkflowStatus,
    WorkflowStepResult,
)
from agent_workflow.workflow_result import WorkflowResult

from application.models import (
    ExecutionModel,
    ResultModel,
    RunModel,
    SnapshotModel,
)
from application.services import (
    ExecutionService,
    ResultService,
    RunService,
    SnapshotService,
)


class ApplicationStateUpdateM1854Tests(unittest.TestCase):
    """Verify Application DTOs reflect updated Core state."""

    # ------------------------------------------------------------------
    # Run state update
    # ------------------------------------------------------------------

    def test_run_state_update_produces_new_application_model(self):
        first_core = Run(
            run_id="run-001",
            task_id="task-001",
        )

        second_core = Run(
            run_id="run-002",
            task_id="task-002",
        )

        first_model = RunService.from_core(first_core)
        second_model = RunService.from_core(second_core)

        self.assertIsInstance(first_model, RunModel)
        self.assertIsInstance(second_model, RunModel)

        self.assertEqual(first_model.run_id, "run-001")
        self.assertEqual(first_model.task_id, "task-001")

        self.assertEqual(second_model.run_id, "run-002")
        self.assertEqual(second_model.task_id, "task-002")

        self.assertIsNot(first_model, second_model)

    # ------------------------------------------------------------------
    # Execution state update
    # ------------------------------------------------------------------

    def test_execution_state_update_is_reflected(self):
        first_core = Execution(
            run_id="run-001",
            status="IN_PROGRESS",
        )

        second_core = Execution(
            run_id="run-001",
            status="COMPLETED",
        )

        first_model = ExecutionService.from_core(first_core)
        second_model = ExecutionService.from_core(second_core)

        self.assertEqual(first_model.status, "IN_PROGRESS")
        self.assertEqual(second_model.status, "COMPLETED")

        self.assertIsNot(first_model, second_model)

    # ------------------------------------------------------------------
    # Result state update
    # ------------------------------------------------------------------

    def test_result_state_update_is_reflected(self):
        first_core = Result(
            run_id="run-001",
            status="IN_PROGRESS",
        )

        second_core = Result(
            run_id="run-001",
            status="COMPLETED",
        )

        first_model = ResultService.from_core(first_core)
        second_model = ResultService.from_core(second_core)

        self.assertIsInstance(first_model, ResultModel)
        self.assertIsInstance(second_model, ResultModel)

        self.assertEqual(first_model.status, "IN_PROGRESS")
        self.assertEqual(second_model.status, "COMPLETED")

        self.assertIsNot(first_model, second_model)

    # ------------------------------------------------------------------
    # WorkflowResult state update
    # ------------------------------------------------------------------

    def test_workflow_result_update_is_reflected(self):
        successful = WorkflowStepResult(
            operation="inspect",
            status=WorkflowStatus.COMPLETED,
            result="ok",
            success=True,
        )

        failed = WorkflowStepResult(
            operation="modify",
            status=WorkflowStatus.FAILED,
            result="failed",
            success=False,
        )

        first_core = WorkflowResult.from_step_results(
            (successful,),
            run_id="run-001",
        )

        second_core = WorkflowResult.from_step_results(
            (successful, failed),
            run_id="run-001",
        )

        first_model = ResultService.from_workflow_result(first_core)
        second_model = ResultService.from_workflow_result(second_core)

        self.assertEqual(first_model.status, "COMPLETED")
        self.assertEqual(first_model.total_steps, 1)
        self.assertEqual(first_model.successful_steps, 1)
        self.assertEqual(first_model.failed_steps, 0)
        self.assertTrue(first_model.completed_successfully)

        self.assertEqual(second_model.status, "FAILED")
        self.assertEqual(second_model.total_steps, 2)
        self.assertEqual(second_model.successful_steps, 1)
        self.assertEqual(second_model.failed_steps, 1)
        self.assertFalse(second_model.completed_successfully)
        self.assertEqual(second_model.failure_index, 1)

        self.assertIsNot(first_model, second_model)

    # ------------------------------------------------------------------
    # Snapshot state update
    # ------------------------------------------------------------------

    def test_snapshot_state_update_is_reflected(self):
        run_status = next(iter(RunStatus))
        step_status = next(iter(StepStatus))

        first_core = ExecutionSnapshot(
            run_id="run-001",
            task_id="task-001",
            run_status=run_status,
            step_states={
                "step-001": step_status,
            },
            current_step=None,
            started_at=None,
            finished_at=None,
        )

        second_core = ExecutionSnapshot(
            run_id="run-001",
            task_id="task-001",
            run_status=run_status,
            step_states={
                "step-001": step_status,
            },
            current_step="step-001",
            started_at="started",
            finished_at=None,
        )

        first_model = SnapshotService.from_core(first_core)
        second_model = SnapshotService.from_core(second_core)

        self.assertIsInstance(first_model, SnapshotModel)
        self.assertIsInstance(second_model, SnapshotModel)

        self.assertIsNone(first_model.current_step)
        self.assertIsNone(first_model.started_at)

        self.assertEqual(second_model.current_step, "step-001")
        self.assertEqual(second_model.started_at, "started")

        self.assertIsNot(first_model, second_model)

    # ------------------------------------------------------------------
    # Snapshot step-state update
    # ------------------------------------------------------------------

    def test_snapshot_step_state_update_is_reflected(self):
        run_status = next(iter(RunStatus))
        step_statuses = list(StepStatus)

        initial_step_status = step_statuses[0]
        updated_step_status = (
            step_statuses[1]
            if len(step_statuses) > 1
            else step_statuses[0]
        )

        first_core = ExecutionSnapshot(
            run_id="run-001",
            task_id="task-001",
            run_status=run_status,
            step_states={
                "step-001": initial_step_status,
            },
            current_step="step-001",
            started_at=None,
            finished_at=None,
        )

        second_core = ExecutionSnapshot(
            run_id="run-001",
            task_id="task-001",
            run_status=run_status,
            step_states={
                "step-001": updated_step_status,
            },
            current_step="step-001",
            started_at=None,
            finished_at=None,
        )

        first_model = SnapshotService.from_core(first_core)
        second_model = SnapshotService.from_core(second_core)

        self.assertEqual(
            first_model.step_states["step-001"],
            initial_step_status.value,
        )

        self.assertEqual(
            second_model.step_states["step-001"],
            updated_step_status.value,
        )

        self.assertIsNot(first_model.step_states, second_model.step_states)

    # ------------------------------------------------------------------
    # Previous DTO isolation
    # ------------------------------------------------------------------

    def test_previous_dto_does_not_change_when_new_core_state_is_mapped(self):
        first_core = Execution(
            run_id="run-001",
            status="IN_PROGRESS",
        )

        first_model = ExecutionService.from_core(first_core)

        updated_core = Execution(
            run_id="run-001",
            status="COMPLETED",
        )

        second_model = ExecutionService.from_core(updated_core)

        self.assertEqual(first_model.status, "IN_PROGRESS")
        self.assertEqual(second_model.status, "COMPLETED")

    # ------------------------------------------------------------------
    # DTO immutability
    # ------------------------------------------------------------------

    def test_updated_dtos_remain_immutable(self):
        core = Execution(
            run_id="run-001",
            status="COMPLETED",
        )

        model = ExecutionService.from_core(core)

        with self.assertRaises(FrozenInstanceError):
            model.status = "FAILED"

    # ------------------------------------------------------------------
    # Core object isolation
    # ------------------------------------------------------------------

    def test_state_update_does_not_return_core_objects(self):
        run_model = RunService.from_core(
            Run(
                run_id="run-001",
                task_id="task-001",
            )
        )

        execution_model = ExecutionService.from_core(
            Execution(
                run_id="run-001",
                status="COMPLETED",
            )
        )

        result_model = ResultService.from_core(
            Result(
                run_id="run-001",
                status="COMPLETED",
            )
        )

        self.assertNotIsInstance(run_model, Run)
        self.assertNotIsInstance(execution_model, Execution)
        self.assertNotIsInstance(result_model, Result)

    # ------------------------------------------------------------------
    # Invalid state update inputs
    # ------------------------------------------------------------------

    def test_invalid_run_update_input_is_rejected(self):
        with self.assertRaises(TypeError):
            RunService.from_core(object())

    def test_invalid_execution_update_input_is_rejected(self):
        with self.assertRaises(TypeError):
            ExecutionService.from_core(object())

    def test_invalid_result_update_input_is_rejected(self):
        with self.assertRaises(TypeError):
            ResultService.from_core(object())

    def test_invalid_workflow_result_update_input_is_rejected(self):
        with self.assertRaises(TypeError):
            ResultService.from_workflow_result(object())

    def test_invalid_snapshot_update_input_is_rejected(self):
        with self.assertRaises(TypeError):
            SnapshotService.from_core(object())


if __name__ == "__main__":
    unittest.main()