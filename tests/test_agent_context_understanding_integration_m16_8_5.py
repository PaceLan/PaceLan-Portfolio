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


class AgentContextUnderstandingIntegrationM1685Tests(unittest.TestCase):

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

    def test_project_summary_matches_context(self):
        summary = self.project_context_agent.project_summary

        self.assertEqual(
            summary.root_path,
            self.project_root.resolve(),
        )
        self.assertEqual(summary.total_files, 2)
        self.assertEqual(summary.python_files, 2)

    def test_context_understanding_extracts_task_identity(self):
        task = WorkflowTask(
            task_id="task-m1685",
            project_id="project-m1685",
            description="inspect main.py",
            context="target: main.py",
        )

        understanding = (
            self.project_context_agent
            .context_understanding
            .understand_task(task)
        )

        self.assertEqual(
            understanding.task.task_id,
            task.task_id,
        )
        self.assertEqual(
            understanding.task.project_id,
            task.project_id,
        )
        self.assertEqual(
            understanding.task.target,
            "main.py",
        )

    def test_context_understanding_selects_target_file(self):
        task = WorkflowTask(
            task_id="task-m1685-target",
            project_id="project-m1685",
            description="inspect project",
            context="target: main.py",
        )

        understanding = (
            self.project_context_agent
            .context_understanding
            .understand_task(task)
        )

        self.assertEqual(
            understanding.relevant_files,
            (Path("main.py"),),
        )

    def test_context_understanding_provides_structured_summary(self):
        task = WorkflowTask(
            task_id="task-m1685-summary",
            project_id="project-m1685",
            description="inspect main.py",
            context="target: main.py",
        )

        understanding = (
            self.project_context_agent
            .context_understanding
            .understand_task(task)
        )

        structured = understanding.structured_summary

        self.assertIsNotNone(structured)
        self.assertEqual(
            structured.task_id,
            task.task_id,
        )
        self.assertEqual(
            structured.project_id,
            task.project_id,
        )
        self.assertEqual(
            structured.target,
            "main.py",
        )
        self.assertEqual(
            structured.relevant_file_count,
            1,
        )

    def test_agent_service_preserves_context_understanding(self):
        task = WorkflowTask(
            task_id="task-m1685-agent",
            project_id="project-m1685",
            description="inspect main.py",
            context="target: main.py",
        )

        execution = self.agent_service.run(task)

        self.assertIsNotNone(
            execution.context_understanding
        )

        self.assertEqual(
            execution.context_understanding.task.task_id,
            task.task_id,
        )

        self.assertEqual(
            execution.context_understanding.task.project_id,
            task.project_id,
        )

        self.assertEqual(
            execution.context_understanding.task.target,
            "main.py",
        )

        self.assertEqual(
            execution.context_understanding.relevant_files,
            (Path("main.py"),),
        )


if __name__ == "__main__":
    unittest.main()
