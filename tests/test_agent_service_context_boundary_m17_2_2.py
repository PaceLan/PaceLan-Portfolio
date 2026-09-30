import tempfile
import unittest
from pathlib import Path

from agent_workflow.agent_service import AgentExecution, AgentService
from agent_workflow.context_understanding import ContextUnderstandingResult
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import AgentWorkflow, WorkflowTask
from agent_workflow.workflow_plan import WorkflowStep
from agent_workflow.workflow_service import WorkflowService
from history.history_core import HistoryStore
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class AgentServiceContextBoundaryM1722Tests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        (root / "sample.py").write_text(
            "value = 1\n",
            encoding="utf-8",
        )

        scanner = ProjectScanner(root)
        scan_result = scanner.scan()

        project_context = ProjectContextBuilder().build(
            scan_result
        )

        self.project_context_agent = ProjectContextAgentInterface(
            project_context
        )

        history_store = HistoryStore(
            root / "history.json"
        )
        snapshot_store = SnapshotStore(
            root,
            root / "snapshots",
        )
        snapshot_service = SnapshotService(
            root,
            store=snapshot_store,
        )

        workflow = AgentWorkflow(
            history_store=history_store,
            snapshot_service=snapshot_service,
        )

        workflow_service = WorkflowService(workflow)

        self.service = AgentService(
            workflow_service,
            project_context_agent=self.project_context_agent,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def task(self):
        return WorkflowTask(
            task_id="task-001",
            description="Run context boundary task",
        )

    def steps(self):
        return (
            WorkflowStep(
                operation="step_1",
                action=lambda: "one",
            ),
        )

    def test_context_understanding_does_not_replace_requested_task(self):
        task = self.task()

        execution = self.service.run(
            task,
            self.steps(),
        )

        self.assertEqual(
            execution.context_understanding.task.task_id,
            task.task_id,
        )

        self.assertEqual(
            execution.context_understanding.task.description,
            task.description,
        )

    def test_context_understanding_does_not_change_plan_steps(self):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        planned_step = execution.plan.steps[0]

        self.assertEqual(
            planned_step.operation,
            "step_1",
        )
        self.assertEqual(
            planned_step.action(),
            "one",
        )
        self.assertEqual(
            planned_step.risk.value,
            "SAFE",
        )
        self.assertEqual(
            planned_step.approval.value,
            "NOT_REQUESTED",
        )
        self.assertEqual(
            planned_step.target,
            ".",
        )
        self.assertIsNone(
            planned_step.context,
        )
        self.assertEqual(
            planned_step.step_id,
            "step-001",
        )
    def test_context_aware_execution_preserves_execution_result(self):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        self.assertEqual(
            execution.result.status.value,
            "COMPLETED",
        )

    def test_context_understanding_is_observational_only(self):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        context = execution.context_understanding

        self.assertIsInstance(
            context,
            ContextUnderstandingResult,
        )

        self.assertIsNot(
            context,
            execution.plan,
        )

        self.assertIsNot(
            context,
            execution.result,
        )

    def test_context_agent_identity_is_preserved(self):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        self.assertIs(
            execution.project_context_agent,
            self.project_context_agent,
        )

    def test_context_boundary_does_not_break_execution_observations(self):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        self.assertIsInstance(
            execution,
            AgentExecution,
        )
        self.assertIsNotNone(execution.run_context)
        self.assertIsNotNone(execution.result)
        self.assertIsNotNone(execution.analysis)
        self.assertIsNotNone(execution.snapshot)
        self.assertIsNotNone(execution.summary)

    def test_context_understanding_matches_requested_task_identity(self):
        task = self.task()

        execution = self.service.run(
            task,
            self.steps(),
        )

        self.assertEqual(
            execution.context_understanding.task.task_id,
            task.task_id,
        )

        self.assertEqual(
            execution.context_understanding.task.description,
            task.description,
        )

    def test_context_boundary_does_not_add_execution_side_effects(self):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        self.assertEqual(
            execution.plan.steps[0].operation,
            "step_1",
        )

        self.assertEqual(
            execution.plan.steps[0].step_id,
            "step-001",
        )

        self.assertEqual(
            execution.result.status.value,
            "COMPLETED",
        )


if __name__ == "__main__":
    unittest.main()


