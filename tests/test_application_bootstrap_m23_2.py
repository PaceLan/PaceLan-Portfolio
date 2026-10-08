import tempfile
import unittest
from pathlib import Path

from agent_workflow.agent_service import AgentService
from agent_workflow.workflow_core import AgentWorkflow
from agent_workflow.workflow_service import WorkflowService
from application.bootstrap import (
    ApplicationBootstrap,
    ApplicationRuntime,
    BootstrapState,
)
from application.runtime_authority import RuntimeAuthority
from application.services import ApplicationExecutionService
from application.workspace import ProjectWorkspaceService
from history.history_core import HistoryStore
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class TestM23_2ApplicationBootstrap(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_root = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def _build_agent_service(self):
        history_store = HistoryStore(self.project_root / "history.json")
        snapshot_store = SnapshotStore(
            self.project_root,
            self.project_root / "snapshots",
        )
        snapshot_service = SnapshotService(
            self.project_root,
            store=snapshot_store,
        )
        workflow = AgentWorkflow(
            history_store=history_store,
            snapshot_service=snapshot_service,
        )
        workflow_service = WorkflowService(workflow)
        return AgentService(workflow_service)

    def test_create_returns_application_runtime(self):
        runtime = ApplicationBootstrap.create(self.project_root)
        self.assertIsInstance(runtime, ApplicationRuntime)
        self.assertIsInstance(runtime.agent_service, AgentService)
        self.assertIsInstance(
            runtime.execution_service,
            ApplicationExecutionService,
        )
        self.assertIsInstance(
            runtime.runtime_authority,
            RuntimeAuthority,
        )
        self.assertIs(
            runtime.execution_service.runtime_authority,
            runtime.runtime_authority,
        )

    def test_create_reuses_supplied_agent_service(self):
        agent_service = self._build_agent_service()
        runtime = ApplicationBootstrap.create(
            self.project_root,
            agent_service=agent_service,
        )
        self.assertIs(runtime.agent_service, agent_service)

    def test_runtime_is_immutable(self):
        runtime = ApplicationBootstrap.create(self.project_root)
        with self.assertRaises(Exception):
            runtime.agent_service = runtime.agent_service

    def test_runtime_reaches_ready(self):
        runtime = ApplicationBootstrap.create(self.project_root)
        self.assertEqual(runtime.state, BootstrapState.READY)

    def test_runtime_exposes_workspace_service(self):
        runtime = ApplicationBootstrap.create(self.project_root)
        self.assertIsInstance(
            runtime.workspace_service,
            ProjectWorkspaceService,
        )

    def test_bootstrap_returns_ready_runtime(self):
        runtime = ApplicationBootstrap.bootstrap(self.project_root)
        self.assertEqual(runtime.state, BootstrapState.READY)
        self.assertIsNone(runtime.error)

    def test_invalid_project_root_is_rejected(self):
        with self.assertRaises(ValueError):
            ApplicationBootstrap.create(
                self.project_root / "missing",
            )

    def test_file_project_root_is_rejected(self):
        project_file = self.project_root / "project.txt"
        project_file.write_text("test", encoding="utf-8")

        with self.assertRaises(ValueError):
            ApplicationBootstrap.create(project_file)


if __name__ == "__main__":
    unittest.main()
