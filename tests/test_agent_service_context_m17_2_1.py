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
from agent_workflow.workflow_core import AgentWorkflow
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowStep
from agent_workflow.workflow_service import WorkflowService
from history.history_core import HistoryStore
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class AgentServiceContextM1721Tests(unittest.TestCase):

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
            description="Run context-aware task",
        )

    def steps(self):
        return (
            WorkflowStep(
                operation="step_1",
                action=lambda: "one",
            ),
        )

    def test_context_agent_is_preserved_in_agent_execution(self):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        self.assertIsInstance(
            execution,
            AgentExecution,
        )
        self.assertIs(
            execution.project_context_agent,
            self.project_context_agent,
        )

    def test_context_understanding_is_created_when_context_agent_exists(
        self,
    ):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        self.assertIsNotNone(
            execution.context_understanding,
        )
        self.assertIsInstance(
            execution.context_understanding,
            ContextUnderstandingResult,
        )

    def test_context_understanding_belongs_to_requested_task(self):
        task = self.task()

        execution = self.service.run(
            task,
            self.steps(),
        )

        self.assertEqual(
            execution.context_understanding.task.task_id,
            task.task_id,
        )

    def test_context_aware_execution_still_produces_execution_observation(
        self,
    ):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        self.assertIsNotNone(
            execution.run_context,
        )
        self.assertIsNotNone(
            execution.result,
        )
        self.assertIsNotNone(
            execution.snapshot,
        )
        self.assertIsNotNone(
            execution.summary,
        )

    def test_context_understanding_is_absent_without_context_agent(self):
        root = Path(self.temp_dir.name)

        history_store = HistoryStore(
            root / "history-no-context.json",
        )
        snapshot_store = SnapshotStore(
            root,
            root / "snapshots-no-context",
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
        service = AgentService(workflow_service)

        execution = service.run(
            self.task(),
            self.steps(),
        )

        self.assertIsNone(
            execution.project_context_agent,
        )
        self.assertIsNone(
            execution.context_understanding,
        )


if __name__ == "__main__":
    unittest.main()