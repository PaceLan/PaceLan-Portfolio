import tempfile
import unittest
from pathlib import Path

from application.commands import ExecuteTaskCommand, ExecuteTaskHandler
from application.models import ApplicationExecutionModel, TaskModel
from application.services import ApplicationExecutionService
from application.runtime_authority import RuntimeAuthority

from agent_workflow.agent_service import AgentService
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import AgentWorkflow
from agent_workflow.workflow_plan import WorkflowStep
from agent_workflow.workflow_service import WorkflowService

from history.history_core import HistoryStore
from snapshots.snapshot_service import SnapshotService


class ApplicationCommandM1874Tests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        root = Path(__file__).resolve().parents[1]

        scan_result = ProjectScanner(root).scan()
        context = ProjectContextBuilder().build(scan_result)
        agent = ProjectContextAgentInterface(context)

        cls._temp_directory = tempfile.TemporaryDirectory()
        storage_root = Path(cls._temp_directory.name)

        history_store = HistoryStore(
            storage_root / "history",
        )

        snapshot_service = SnapshotService(
            root,
            snapshot_directory=storage_root / "snapshots",
        )

        workflow = AgentWorkflow(
            history_store=history_store,
            snapshot_service=snapshot_service,
        )

        workflow_service = WorkflowService(workflow)

        agent_service = AgentService(
            workflow_service,
            project_context_agent=agent,
        )

        execution_service = ApplicationExecutionService(
            agent_service,
            runtime_authority=RuntimeAuthority(),
        )

        cls.handler = ExecuteTaskHandler(
            execution_service,
        )

    @classmethod
    def tearDownClass(cls):
        cls._temp_directory.cleanup()

    def test_handler_returns_application_execution_model(self):
        task = TaskModel(
            task_id="task-001",
            project_id="project-001",
            description="execute application command",
        )

        result = self.handler.handle(
            ExecuteTaskCommand(task=task)
        )

        self.assertIsInstance(
            result,
            ApplicationExecutionModel,
        )

    def test_handler_preserves_task_identity(self):
        task = TaskModel(
            task_id="task-002",
            project_id="project-002",
        )

        result = self.handler.handle(
            ExecuteTaskCommand(task=task)
        )

        self.assertEqual(
            result.task.task_id,
            "task-002",
        )
        self.assertEqual(
            result.task.project_id,
            "project-002",
        )
        self.assertEqual(
            result.plan.task_id,
            "task-002",
        )
        self.assertEqual(
            result.plan.project_id,
            "project-002",
        )
        self.assertEqual(
            result.run.task_id,
            "task-002",
        )

    def test_handler_result_contains_no_core_objects(self):
        task = TaskModel(
            task_id="task-003",
            project_id="project-003",
        )

        result = self.handler.handle(
            ExecuteTaskCommand(task=task)
        )

        forbidden_types = {
            "WorkflowTask",
            "WorkflowPlan",
            "WorkflowResult",
            "ExecutionSnapshot",
            "WorkflowStep",
            "ExecutionTracker",
            "AgentExecution",
        }

        values = (
            result,
            result.task,
            result.plan,
            result.run,
            result.result,
            result.snapshot,
        )

        for value in values:
            self.assertNotIn(
                type(value).__name__,
                forbidden_types,
            )

    def test_handler_preserves_result_snapshot_identity(self):
        task = TaskModel(
            task_id="task-004",
            project_id="project-004",
        )

        result = self.handler.handle(
            ExecuteTaskCommand(task=task)
        )

        self.assertEqual(
            result.result.run_id,
            result.run.run_id,
        )
        self.assertEqual(
            result.snapshot.run_id,
            result.run.run_id,
        )

    def test_handler_maps_run_context_to_application_run(self):
        task = TaskModel(
            task_id="task-005",
            project_id="project-005",
        )

        result = self.handler.handle(
            ExecuteTaskCommand(task=task)
        )

        self.assertIsInstance(
            result.run.run_id,
            str,
        )
        self.assertTrue(
            result.run.run_id,
        )
        self.assertEqual(
            result.run.task_id,
            "task-005",
        )

    def test_handler_exposes_snapshot_finished_at(self):
        task = TaskModel(
            task_id="task-006",
            project_id="project-006",
        )

        result = self.handler.handle(
            ExecuteTaskCommand(task=task)
        )

        self.assertTrue(
            hasattr(result.snapshot, "finished_at"),
        )


if __name__ == "__main__":
    unittest.main()