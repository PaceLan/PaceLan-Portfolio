import tempfile
import unittest
from pathlib import Path

from agent_workflow.agent_service import AgentService
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import AgentWorkflow
from agent_workflow.workflow_plan import WorkflowStep
from agent_workflow.workflow_service import WorkflowService
from application.services import ApplicationExecutionService
from application.history_storage import AgentHistoryStorage
from application.models import TaskModel
from history.history_core import HistoryStore
from snapshots.snapshot_service import SnapshotService


from application.runtime_authority import RuntimeAuthority
class ApplicationExecutionPersistenceB3Tests(unittest.TestCase):

    def test_execution_persists_agent_history(self):
        root = Path(__file__).resolve().parents[1]

        with tempfile.TemporaryDirectory() as directory:
            storage_root = Path(directory)

            scan_result = ProjectScanner(root).scan()
            context = ProjectContextBuilder().build(scan_result)
            context_agent = ProjectContextAgentInterface(context)

            workflow = AgentWorkflow(
                history_store=HistoryStore(storage_root / "history"),
                snapshot_service=SnapshotService(
                    root,
                    snapshot_directory=storage_root / "snapshots",
                ),
            )

            service = ApplicationExecutionService(
                AgentService(
                    WorkflowService(workflow),
                    project_context_agent=context_agent,
                ),
                project_path=storage_root,
            runtime_authority=RuntimeAuthority(),
            )

            execution = service.run(
                TaskModel(
                    task_id="b3-task",
                    project_id="b3-project",
                ),
                steps=(
                    WorkflowStep(
                        operation="verify",
                        action=lambda: "ok",
                        step_id="b3-step",
                    ),
                ),
            )

            self.assertIsNotNone(execution.verification)
            self.assertEqual(
                execution.verification.run_id,
                execution.run.run_id,
            )

            entries = AgentHistoryStorage().load(storage_root)

            self.assertEqual(len(entries), 1)
            self.assertEqual(entries[0].task_id, "b3-task")
            self.assertEqual(entries[0].project_id, "b3-project")
            self.assertEqual(
                entries[0].execution_id,
                execution.run.run_id,
            )


if __name__ == "__main__":
    unittest.main()
