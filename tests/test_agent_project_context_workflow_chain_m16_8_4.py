import tempfile
import unittest
from pathlib import Path

from agent_workflow.agent_service import AgentService
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import AgentWorkflow, WorkflowTask
from agent_workflow.workflow_service import WorkflowService

from history.history_core import HistoryStore
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class AgentProjectContextWorkflowChainM1684Tests(unittest.TestCase):

    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)

        self.project_root = root / "project"
        self.snapshot_root = root / "snapshots"
        self.history_root = root / "history"

        self.project_root.mkdir()
        self.history_root.mkdir()

        (self.project_root / "main.py").write_text(
            "from helper import run\n\nrun()\n",
            encoding="utf-8",
        )

        (self.project_root / "helper.py").write_text(
            "def run():\n"
            "    return 'ok'\n",
            encoding="utf-8",
        )

        snapshot_store = SnapshotStore(
            self.project_root.resolve(),
            self.snapshot_root,
        )

        workflow = AgentWorkflow(
            HistoryStore(self.history_root),
            SnapshotService(
                self.project_root.resolve(),
                store=snapshot_store,
            ),
        )

        self.workflow_service = WorkflowService(workflow)

        scan_result = ProjectScanner(self.project_root).scan()
        context = ProjectContextBuilder().build(scan_result)

        self.project_context_agent = ProjectContextAgentInterface(
            context
        )

        self.agent_service = AgentService(
            self.workflow_service,
            project_context_agent=self.project_context_agent,
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_agent_service_accepts_project_context_interface(self):
        self.assertIs(
            self.agent_service.project_context_agent,
            self.project_context_agent,
        )

    def test_project_context_interface_exposes_context_and_query(self):
        self.assertIs(
            self.project_context_agent.context,
            self.project_context_agent.query.context,
        )

        self.assertEqual(
            self.project_context_agent.context.root_path,
            self.project_root.resolve(),
        )

    def test_project_context_query_sees_scanned_python_file(self):
        main_file = self.project_context_agent.query.get_file(
            "main.py"
        )

        self.assertIsNotNone(main_file)
        self.assertEqual(main_file.name, "main.py")
        self.assertEqual(main_file.extension, ".py")

    def test_agent_service_run_preserves_result_identity(self):
        task = WorkflowTask(
            task_id="task-m1684",
            project_id="project-m1684",
            description="inspect project",
        )

        execution = self.agent_service.run(task)

        self.assertIsNotNone(execution)
        self.assertIsNotNone(execution.result)
        self.assertEqual(
            execution.result.run_id,
            execution.run_context.run_id,
        )


if __name__ == "__main__":
    unittest.main()