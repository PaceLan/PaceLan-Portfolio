"""M18.4 application state and DTO boundary tests."""

from dataclasses import FrozenInstanceError

import unittest

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


class ApplicationStateM184Tests(unittest.TestCase):
    def test_application_state_models_are_immutable(self):
        run = RunModel("run-001", "task-001")
        execution = ExecutionModel("run-001", "COMPLETED")
        result = ResultModel("run-001", "COMPLETED")
        snapshot = SnapshotModel(
            run_id="run-001",
            task_id="task-001",
            run_status="COMPLETED",
            step_states={"step-001": "COMPLETED"},
        )

        with self.assertRaises(FrozenInstanceError):
            run.run_id = "run-002"

        with self.assertRaises(FrozenInstanceError):
            execution.status = "FAILED"

        with self.assertRaises(FrozenInstanceError):
            result.status = "FAILED"

        with self.assertRaises(FrozenInstanceError):
            snapshot.run_status = "FAILED"

    def test_snapshot_step_states_are_immutable(self):
        snapshot = SnapshotModel(
            run_id="run-001",
            task_id="task-001",
            run_status="COMPLETED",
            step_states={"step-001": "COMPLETED"},
        )

        with self.assertRaises(TypeError):
            snapshot.step_states["step-002"] = "FAILED"

    def test_run_service_maps_core_identity_only(self):
        core = Run(
            run_id="run-001",
            task_id="task-001",
        )

        model = RunService.from_core(core)

        self.assertIsInstance(model, RunModel)
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.task_id, "task-001")
        self.assertFalse(hasattr(model, "action"))

    def test_execution_service_maps_core_state_only(self):
        core = Execution(
            run_id="run-001",
            status="IN_PROGRESS",
        )

        model = ExecutionService.from_core(core)

        self.assertIsInstance(model, ExecutionModel)
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.status, "IN_PROGRESS")
        self.assertFalse(hasattr(model, "action"))

    def test_result_service_maps_minimal_core_result(self):
        core = Result(
            run_id="run-001",
            status="FAILED",
        )

        model = ResultService.from_core(core)

        self.assertIsInstance(model, ResultModel)
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.status, "FAILED")
        self.assertEqual(model.total_steps, 0)
        self.assertEqual(model.successful_steps, 0)
        self.assertEqual(model.failed_steps, 0)
        self.assertEqual(model.blocked_steps, 0)
        self.assertFalse(model.completed_successfully)
        self.assertIsNone(model.failure_index)

    def test_result_service_maps_workflow_result_without_core_leak(self):
        step_results = (
            WorkflowStepResult(
                operation="inspect",
                status=WorkflowStatus.COMPLETED,
                result="ok",
                success=True,
            ),
            WorkflowStepResult(
                operation="modify",
                status=WorkflowStatus.FAILED,
                result="ValueError",
                success=False,
            ),
        )

        workflow_result = WorkflowResult.from_step_results(
            step_results,
            run_id="run-001",
        )

        model = ResultService.from_workflow_result(
            workflow_result,
        )

        self.assertIsInstance(model, ResultModel)
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.status, "FAILED")
        self.assertEqual(model.total_steps, 2)
        self.assertEqual(model.successful_steps, 1)
        self.assertEqual(model.failed_steps, 1)
        self.assertEqual(model.blocked_steps, 0)
        self.assertFalse(model.completed_successfully)
        self.assertEqual(model.failure_index, 1)

        self.assertFalse(hasattr(model, "step_results"))
        self.assertFalse(hasattr(model, "action"))

    def test_snapshot_service_maps_full_execution_state(self):
        run_status = next(iter(RunStatus))
        step_status = next(iter(StepStatus))

        core = ExecutionSnapshot(
            run_id="run-001",
            task_id="task-001",
            run_status=run_status,
            step_states={
                "step-001": step_status,
            },
            current_step="step-001",
            started_at=None,
            finished_at=None,
        )

        model = SnapshotService.from_core(core)

        self.assertIsInstance(model, SnapshotModel)
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.task_id, "task-001")
        self.assertEqual(model.run_status, run_status.value)
        self.assertEqual(
            model.step_states["step-001"],
            step_status.value,
        )
        self.assertEqual(model.current_step, "step-001")
        self.assertIsNone(model.started_at)
        self.assertIsNone(model.finished_at)

    def test_snapshot_conversion_does_not_leak_core_snapshot(self):
        run_status = next(iter(RunStatus))
        step_status = next(iter(StepStatus))

        core = ExecutionSnapshot(
            run_id="run-001",
            task_id="task-001",
            run_status=run_status,
            step_states={"step-001": step_status},
            current_step=None,
            started_at=None,
            finished_at=None,
        )

        model = SnapshotService.from_core(core)

        self.assertNotIsInstance(
            model.step_states["step-001"],
            StepStatus,
        )
        self.assertNotIsInstance(
            model.run_status,
            RunStatus,
        )

    def test_invalid_run_input_is_rejected(self):
        with self.assertRaises(TypeError):
            RunService.from_core(object())

    def test_invalid_execution_input_is_rejected(self):
        with self.assertRaises(TypeError):
            ExecutionService.from_core(object())

    def test_invalid_result_input_is_rejected(self):
        with self.assertRaises(TypeError):
            ResultService.from_core(object())

    def test_invalid_workflow_result_input_is_rejected(self):
        with self.assertRaises(TypeError):
            ResultService.from_workflow_result(object())

    def test_invalid_snapshot_input_is_rejected(self):
        with self.assertRaises(TypeError):
            SnapshotService.from_core(object())


if __name__ == "__main__":
    unittest.main()