import tempfile
import unittest
from pathlib import Path

from application import (
    PlanModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    TaskModel,
)
from application.models import ApplicationExecutionModel
from application.services import ApplicationExecutionService
from agent_workflow.agent_service import AgentService
from agent_workflow.workflow_core import AgentWorkflow
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_service import WorkflowService
from agent_workflow.workflow_plan import WorkflowStep
from history.history_core import HistoryStore
from snapshots.snapshot_service import SnapshotService


class ApplicationExecutionFacadeM1865Tests(unittest.TestCase):

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

        cls.service = ApplicationExecutionService(agent_service)

    @classmethod
    def tearDownClass(cls):
        cls._temp_directory.cleanup()

    def test_run_returns_application_execution_model(self):
        task = TaskModel(
            task_id="task-001",
            project_id="project-001",
            description="application execution test",
            context="test",
        )

        execution = self.service.run(task)

        self.assertIsNotNone(execution)
        self.assertIsInstance(
            execution,
            ApplicationExecutionModel,
        )

        self.assertEqual(
            execution.task.task_id,
            "task-001",
        )
        self.assertEqual(
            execution.task.project_id,
            "project-001",
        )

        self.assertIsInstance(
            execution.plan,
            PlanModel,
        )
        self.assertIsInstance(
            execution.run,
            RunModel,
        )
        self.assertIsInstance(
            execution.result,
            ResultModel,
        )
        self.assertIsInstance(
            execution.snapshot,
            SnapshotModel,
        )

    def test_execution_preserves_identity_chain(self):
        task = TaskModel(
            task_id="task-002",
            project_id="project-002",
        )

        execution = self.service.run(task)

        self.assertEqual(
            execution.task.task_id,
            execution.plan.task_id,
        )
        self.assertEqual(
            execution.task.project_id,
            execution.plan.project_id,
        )
        self.assertEqual(
            execution.run.task_id,
            execution.task.task_id,
        )
        self.assertEqual(
            execution.result.run_id,
            execution.run.run_id,
        )
        self.assertEqual(
            execution.snapshot.run_id,
            execution.run.run_id,
        )

    def test_application_execution_does_not_expose_core_execution(self):
        task = TaskModel(
            task_id="task-003",
            project_id="project-003",
        )

        execution = self.service.run(task)

        forbidden_types = {
            "AgentExecution",
            "WorkflowTask",
            "WorkflowPlan",
            "WorkflowResult",
            "ExecutionSnapshot",
            "ExecutionTracker",
            "WorkflowStep",
        }

        values = (
            execution,
            execution.task,
            execution.plan,
            execution.run,
            execution.result,
            execution.snapshot,
        )

        for value in values:
            self.assertNotIn(
                type(value).__name__,
                forbidden_types,
            )

    def test_application_plan_contains_no_workflow_step_objects(self):
        task = TaskModel(
            task_id="task-004",
            project_id="project-004",
        )

        execution = self.service.run(task)

        for step in execution.plan.steps:
            self.assertNotIsInstance(
                step,
                WorkflowStep,
            )
            self.assertNotIn(
                "action",
                vars(step),
            )

    def test_execution_models_are_detached(self):
        task = TaskModel(
            task_id="task-005",
            project_id="project-005",
        )

        execution = self.service.run(task)

        self.assertIsNot(
            execution.task,
            task,
        )
        self.assertIsNot(
            execution.plan,
            execution.task,
        )

    def test_invalid_task_is_rejected(self):
        with self.assertRaises(TypeError):
            self.service.run("invalid")

    def test_result_and_snapshot_share_run_identity(self):
        task = TaskModel(
            task_id="task-006",
            project_id="project-006",
        )

        execution = self.service.run(task)

        self.assertEqual(
            execution.result.run_id,
            execution.snapshot.run_id,
        )

    def test_application_execution_model_is_immutable(self):
        task = TaskModel(
            task_id="task-007",
            project_id="project-007",
        )

        execution = self.service.run(task)

        with self.assertRaises(Exception):
            execution.task = task


if __name__ == "__main__":
    unittest.main()