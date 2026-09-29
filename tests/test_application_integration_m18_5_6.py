"""M18.5.6 Application <-> Core integration boundary tests."""

import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from agent_workflow.agent_project_planner import AgentProjectPlanner
from agent_workflow.core_interfaces import (
    Execution,
    Project,
    Result,
    Run,
)
from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import (
    WorkflowStatus,
    WorkflowStepResult,
)
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_plan import WorkflowStep

from application.models import (
    ExecutionModel,
    PlanModel,
    ProjectModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    TaskModel,
)
from application.services import (
    ExecutionService,
    PlanningService,
    ProjectService,
    ResultService,
    RunService,
    SnapshotService,
    TaskService,
)


class _StubProjectContextAgent(ProjectContextAgentInterface):
    """Minimal valid ProjectContextAgent implementation."""

    def __init__(self):
        self._temp_dir = tempfile.TemporaryDirectory()
        root = Path(self._temp_dir.name)

        (root / "main.py").write_text(
            "def run():\n"
            "    return True\n",
            encoding="utf-8",
        )

        scan_result = ProjectScanner(root).scan()
        context = ProjectContextBuilder().build(scan_result)

        super().__init__(context=context)

    def close(self):
        self._temp_dir.cleanup()


class ApplicationIntegrationM1856Tests(unittest.TestCase):
    """Verify complete Application/Core integration boundaries."""

    def _create_agent(self):
        agent = _StubProjectContextAgent()
        self.addCleanup(agent.close)
        return agent

    @staticmethod
    def _task_model() -> TaskModel:
        return TaskModel(
            task_id="task-001",
            project_id="project-001",
            description="integration task",
            context="integration context",
        )

    @staticmethod
    def _steps() -> tuple[WorkflowStep, ...]:
        def action() -> str:
            return "ok"

        return (
            WorkflowStep(
                operation="inspect",
                action=action,
                risk="SAFE",
                approval="NOT_REQUESTED",
                target="src/main.py",
                context="inspect source",
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

    # ------------------------------------------------------------------
    # Project / Task application -> Core boundaries
    # ------------------------------------------------------------------

    def test_project_application_to_core_identity_is_preserved(self):
        model = ProjectService.create("project-001")

        self.assertIsInstance(model, ProjectModel)

        core = Project(
            project_id=model.project_id,
        )

        mapped = ProjectService.from_core(core)

        self.assertEqual(mapped.project_id, model.project_id)
        self.assertIsNot(mapped, model)

    def test_task_application_to_core_identity_is_preserved(self):
        model = self._task_model()

        core = TaskService.to_core(model)

        self.assertEqual(core.task_id, model.task_id)
        self.assertEqual(core.project_id, model.project_id)

        mapped = TaskService.from_core(
            core,
            description=model.description,
            context=model.context,
        )

        self.assertEqual(mapped.task_id, model.task_id)
        self.assertEqual(mapped.project_id, model.project_id)
        self.assertEqual(mapped.description, model.description)
        self.assertEqual(mapped.context, model.context)

    def test_task_application_to_workflow_preserves_context(self):
        model = self._task_model()

        workflow_task = TaskService.to_workflow(model)

        self.assertEqual(
            workflow_task.task_id,
            model.task_id,
        )
        self.assertEqual(
            workflow_task.project_id,
            model.project_id,
        )
        self.assertEqual(
            workflow_task.description,
            model.description,
        )
        self.assertEqual(
            workflow_task.context,
            model.context,
        )

    # ------------------------------------------------------------------
    # Planning integration
    # ------------------------------------------------------------------

    def test_planning_service_integrates_application_task_with_core_planner(self):
        agent = self._create_agent()
        service = PlanningService(agent)
        task = self._task_model()

        model = service.plan(
            task,
            self._steps(),
        )

        self.assertIsInstance(model, PlanModel)
        self.assertEqual(model.task_id, task.task_id)
        self.assertEqual(model.project_id, task.project_id)
        self.assertEqual(len(model.steps), 2)

        self.assertEqual(
            model.steps[0].step_id,
            "step-001",
        )
        self.assertEqual(
            model.steps[1].step_id,
            "step-002",
        )

    def test_planning_integration_does_not_execute_actions(self):
        calls: list[str] = []

        def action() -> str:
            calls.append("executed")
            return "ok"

        step = WorkflowStep(
            operation="inspect",
            action=action,
            risk="SAFE",
            approval="NOT_REQUESTED",
            target="src/main.py",
            context="inspect",
            step_id="step-001",
        )

        agent = self._create_agent()
        service = PlanningService(agent)

        model = service.plan(
            self._task_model(),
            (step,),
        )

        self.assertIsInstance(model, PlanModel)
        self.assertEqual(calls, [])

    def test_planning_result_contains_no_workflow_step_objects(self):
        agent = self._create_agent()
        service = PlanningService(agent)

        model = service.plan(
            self._task_model(),
            self._steps(),
        )

        for step in model.steps:
            self.assertNotIsInstance(step, WorkflowStep)

    # ------------------------------------------------------------------
    # Run / Execution integration
    # ------------------------------------------------------------------

    def test_run_core_to_application_preserves_identity(self):
        core = Run(
            run_id="run-001",
            task_id="task-001",
        )

        model = RunService.from_core(core)

        self.assertIsInstance(model, RunModel)
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.task_id, "task-001")

    def test_execution_core_to_application_preserves_state(self):
        core = Execution(
            run_id="run-001",
            status="COMPLETED",
        )

        model = ExecutionService.from_core(core)

        self.assertIsInstance(model, ExecutionModel)
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.status, "COMPLETED")

    # ------------------------------------------------------------------
    # Result integration
    # ------------------------------------------------------------------

    def test_workflow_result_core_to_application_preserves_run_identity(self):
        result = WorkflowStepResult(
            operation="inspect",
            status=WorkflowStatus.COMPLETED,
            result="ok",
            success=True,
        )

        core = WorkflowResult.from_step_results(
            (result,),
            run_id="run-001",
        )

        model = ResultService.from_workflow_result(core)

        self.assertIsInstance(model, ResultModel)
        self.assertEqual(model.run_id, "run-001")
        self.assertEqual(model.status, "COMPLETED")
        self.assertEqual(model.total_steps, 1)
        self.assertEqual(model.successful_steps, 1)
        self.assertEqual(model.failed_steps, 0)
        self.assertTrue(model.completed_successfully)

    def test_failed_workflow_result_remains_failed_at_application_boundary(self):
        result = WorkflowStepResult(
            operation="write",
            status=WorkflowStatus.FAILED,
            result="failed",
            success=False,
        )

        core = WorkflowResult.from_step_results(
            (result,),
            run_id="run-002",
        )

        model = ResultService.from_workflow_result(core)

        self.assertEqual(model.run_id, "run-002")
        self.assertEqual(model.status, "FAILED")
        self.assertEqual(model.failed_steps, 1)
        self.assertFalse(model.completed_successfully)
        self.assertEqual(model.failure_index, 0)

    # ------------------------------------------------------------------
    # Snapshot integration
    # ------------------------------------------------------------------

    def test_snapshot_core_to_application_preserves_execution_identity(self):
        core = ExecutionSnapshot(
            run_id="run-003",
            task_id="task-001",
            run_status=next(iter(RunStatus)),
            step_states={
                "step-001": next(iter(StepStatus)),
            },
            current_step="step-001",
            started_at=datetime.now(),
            finished_at=None,
        )

        model = SnapshotService.from_core(core)

        self.assertIsInstance(model, SnapshotModel)
        self.assertEqual(model.run_id, core.run_id)
        self.assertEqual(model.task_id, core.task_id)
        self.assertEqual(
            set(model.step_states),
            set(core.step_states),
        )
        self.assertEqual(
            model.current_step,
            core.current_step,
        )

    def test_snapshot_application_mapping_is_detached_from_core_mapping(self):
        core = ExecutionSnapshot(
            run_id="run-004",
            task_id="task-001",
            run_status=next(iter(RunStatus)),
            step_states={
                "step-001": next(iter(StepStatus)),
            },
            current_step=None,
            started_at=None,
            finished_at=None,
        )

        model = SnapshotService.from_core(core)

        self.assertIsNot(
            model.step_states,
            core.step_states,
        )

    # ------------------------------------------------------------------
    # Full identity chain
    # ------------------------------------------------------------------

    def test_task_to_plan_to_result_identity_chain(self):
        task = self._task_model()

        agent = self._create_agent()
        planning = PlanningService(agent)

        plan = planning.plan(
            task,
            self._steps(),
        )

        workflow_result = WorkflowResult.from_step_results(
            (
                WorkflowStepResult(
                    operation="inspect",
                    status=WorkflowStatus.COMPLETED,
                    result="ok",
                    success=True,
                ),
            ),
            run_id="run-chain-001",
        )

        result = ResultService.from_workflow_result(
            workflow_result,
        )

        self.assertEqual(
            plan.task_id,
            task.task_id,
        )
        self.assertEqual(
            plan.project_id,
            task.project_id,
        )
        self.assertEqual(
            result.run_id,
            "run-chain-001",
        )


if __name__ == "__main__":
    unittest.main()