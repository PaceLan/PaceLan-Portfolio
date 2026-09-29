"""M18.5.3 Domain -> DTO mapping boundary tests."""

import unittest
from dataclasses import FrozenInstanceError
from enum import Enum

from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep

from application.models import (
    PlanModel,
    ResultModel,
    SnapshotModel,
    StepModel,
)
from application.services import (
    PlanningService,
    ResultService,
    SnapshotService,
)


class _StubProjectContextAgent:
    """Minimal context-agent test double."""

    pass


class TestApplicationMappingM1853(unittest.TestCase):
    """Verify Domain/Core -> Application DTO mapping."""

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _make_plan() -> WorkflowPlan:
        task = WorkflowTask(
            task_id="task-001",
            description="Test task",
            context="Test context",
            project_id="project-001",
        )

        def action() -> str:
            return "executed"

        steps = (
            WorkflowStep(
                operation="read",
                action=action,
                risk="SAFE",
                approval="NOT_REQUESTED",
                target="src/main.py",
                context="read source",
                step_id="step-001",
            ),
            WorkflowStep(
                operation="write",
                action=action,
                risk="SAFE",
                approval="NOT_REQUESTED",
                target="src/output.py",
                context="write output",
                step_id="step-002",
            ),
        )

        return WorkflowPlan(
            task=task,
            steps=steps,
        )

    @staticmethod
    def _make_snapshot() -> ExecutionSnapshot:
        run_status = next(iter(RunStatus))
        step_status = next(iter(StepStatus))

        return ExecutionSnapshot(
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

    # ------------------------------------------------------------------
    # Plan mapping
    # ------------------------------------------------------------------

    def test_plan_mapping_is_complete_and_excludes_action(self):
        plan = self._make_plan()

        model = PlanningService._to_model(plan)

        self.assertIsInstance(model, PlanModel)

        self.assertEqual(model.task_id, "task-001")
        self.assertEqual(model.project_id, "project-001")
        self.assertEqual(len(model.steps), 2)

        first = model.steps[0]

        self.assertIsInstance(first, StepModel)
        self.assertEqual(first.step_id, "step-001")
        self.assertEqual(first.operation, "read")
        self.assertEqual(first.risk, "SAFE")
        self.assertEqual(first.approval, "NOT_REQUESTED")
        self.assertEqual(first.target, "src/main.py")
        self.assertEqual(first.context, "read source")

        # Application DTO must never expose the executable action.
        self.assertFalse(hasattr(first, "action"))
        self.assertFalse("action" in first.__dataclass_fields__)

    def test_plan_mapping_produces_only_application_models(self):
        plan = self._make_plan()

        model = PlanningService._to_model(plan)

        self.assertIsInstance(model, PlanModel)

        for step in model.steps:
            self.assertIsInstance(step, StepModel)

        self.assertIsInstance(model.steps, tuple)

    def test_plan_mapping_does_not_leak_core_objects(self):
        plan = self._make_plan()

        model = PlanningService._to_model(plan)

        self.assertIsNot(model, plan)
        self.assertIsInstance(model, PlanModel)

        for step_model in model.steps:
            self.assertNotIsInstance(step_model, WorkflowStep)

    # ------------------------------------------------------------------
    # Result mapping
    # ------------------------------------------------------------------

    def test_result_mapping_is_complete(self):
        # Empty result is deliberately used here because the actual
        # WorkflowResult factory guarantees a valid WorkflowStatus Enum.
        result = WorkflowResult.from_step_results(
            (),
            run_id="run-result-001",
        )

        model = ResultService.from_workflow_result(result)

        self.assertIsInstance(model, ResultModel)

        self.assertEqual(model.run_id, result.run_id)
        self.assertEqual(model.status, result.status.value)
        self.assertEqual(model.total_steps, result.total_steps)
        self.assertEqual(
            model.successful_steps,
            result.successful_steps,
        )
        self.assertEqual(
            model.failed_steps,
            result.failed_steps,
        )
        self.assertEqual(
            model.blocked_steps,
            result.blocked_steps,
        )
        self.assertEqual(
            model.completed_successfully,
            result.completed_successfully,
        )
        self.assertEqual(
            model.failure_index,
            result.failure_index,
        )

    def test_result_mapping_does_not_leak_core_object(self):
        result = WorkflowResult.from_step_results(
            (),
            run_id="run-result-002",
        )

        model = ResultService.from_workflow_result(result)

        self.assertIsInstance(model, ResultModel)
        self.assertIsNot(model, result)

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
            self.assertNotIsInstance(value, Enum)

    def test_result_enum_representation_is_string(self):
        result = WorkflowResult.from_step_results(
            (),
            run_id="run-result-003",
        )

        model = ResultService.from_workflow_result(result)

        self.assertIsInstance(model.status, str)
        self.assertEqual(model.status, result.status.value)

    # ------------------------------------------------------------------
    # Snapshot mapping
    # ------------------------------------------------------------------

    def test_snapshot_mapping_is_complete(self):
        snapshot = self._make_snapshot()

        model = SnapshotService.from_core(snapshot)

        self.assertIsInstance(model, SnapshotModel)

        self.assertEqual(model.run_id, snapshot.run_id)
        self.assertEqual(model.task_id, snapshot.task_id)

        expected_run_status = (
            snapshot.run_status.value
            if hasattr(snapshot.run_status, "value")
            else str(snapshot.run_status)
        )

        self.assertEqual(
            model.run_status,
            expected_run_status,
        )

        self.assertEqual(
            model.current_step,
            snapshot.current_step,
        )
        self.assertEqual(
            model.started_at,
            snapshot.started_at,
        )
        self.assertEqual(
            model.finished_at,
            snapshot.finished_at,
        )

        self.assertEqual(
            set(model.step_states.keys()),
            set(snapshot.step_states.keys()),
        )

    def test_snapshot_enum_representations_are_strings(self):
        snapshot = self._make_snapshot()

        model = SnapshotService.from_core(snapshot)

        self.assertIsInstance(model.run_status, str)

        for state in model.step_states.values():
            self.assertIsInstance(state, str)

    def test_snapshot_mapping_does_not_leak_core_snapshot(self):
        snapshot = self._make_snapshot()

        model = SnapshotService.from_core(snapshot)

        self.assertIsInstance(model, SnapshotModel)
        self.assertIsNot(model, snapshot)

        self.assertNotIsInstance(model.run_status, Enum)

        for state in model.step_states.values():
            self.assertNotIsInstance(state, Enum)

    def test_snapshot_step_states_are_detached(self):
        snapshot = self._make_snapshot()

        model = SnapshotService.from_core(snapshot)

        self.assertEqual(
            model.step_states["step-001"],
            snapshot.step_states["step-001"].value,
        )

        # SnapshotModel must own its own mapping rather than exposing
        # the Core snapshot's mapping object.
        self.assertIsNot(
            model.step_states,
            snapshot.step_states,
        )

    # ------------------------------------------------------------------
    # DTO immutability
    # ------------------------------------------------------------------

    def test_dtos_are_immutable(self):
        plan = self._make_plan()
        plan_model = PlanningService._to_model(plan)

        result = WorkflowResult.from_step_results(
            (),
            run_id="run-immutable-001",
        )
        result_model = ResultService.from_workflow_result(result)

        snapshot = self._make_snapshot()
        snapshot_model = SnapshotService.from_core(snapshot)

        with self.assertRaises(FrozenInstanceError):
            plan_model.task_id = "changed"

        with self.assertRaises(FrozenInstanceError):
            result_model.run_id = "changed"

        with self.assertRaises(FrozenInstanceError):
            snapshot_model.run_id = "changed"

    # ------------------------------------------------------------------
    # Application boundary structure
    # ------------------------------------------------------------------

    def test_plan_dto_contains_only_application_step_models(self):
        plan = self._make_plan()

        model = PlanningService._to_model(plan)

        self.assertIsInstance(model, PlanModel)

        for step in model.steps:
            self.assertEqual(type(step), StepModel)

            self.assertEqual(
                set(step.__dataclass_fields__.keys()),
                {
                    "step_id",
                    "operation",
                    "risk",
                    "approval",
                    "target",
                    "context",
                },
            )


if __name__ == "__main__":
    unittest.main()