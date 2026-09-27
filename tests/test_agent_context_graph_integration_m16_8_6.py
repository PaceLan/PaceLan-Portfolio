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


class AgentContextGraphIntegrationM1686Tests(unittest.TestCase):

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

    def _task(self, task_id: str = "task-m1686") -> WorkflowTask:
        return WorkflowTask(
            task_id=task_id,
            project_id="project-m1686",
            description="inspect main.py",
            context="target: main.py",
        )

    def test_relevant_symbols_are_deterministic(self):
        understanding = (
            self.project_context_agent
            .context_understanding
            .understand_task(
                WorkflowTask(
                    task_id="task-m1686-symbols",
                    project_id="project-m1686",
                    description="inspect helper.py",
                    context="target: helper.py",
                )
            )
        )

        self.assertGreaterEqual(
            len(understanding.relevant_symbols),
            1,
        )

        symbol_names = [
            symbol.name
            for symbol in understanding.relevant_symbols
        ]

        self.assertIn("run", symbol_names)

        self.assertEqual(
            understanding.relevant_symbols,
            tuple(
                sorted(
                    understanding.relevant_symbols,
                    key=lambda symbol: (
                        symbol.name,
                        symbol.kind,
                        symbol.lineno,
                    ),
                )
            ),
        )

    def test_relationships_are_derived_from_relevant_context(self):
        understanding = (
            self.project_context_agent
            .context_understanding
            .understand_task(self._task())
        )

        self.assertGreaterEqual(
            len(understanding.relationships),
            1,
        )

        relationship_keys = {
            (
                relationship.source,
                relationship.target,
                relationship.kind,
            )
            for relationship in understanding.relationships
        }

        self.assertEqual(
            len(relationship_keys),
            len(understanding.relationships),
        )

    def test_dependencies_are_sorted_and_unique(self):
        understanding = (
            self.project_context_agent
            .context_understanding
            .understand_task(self._task())
        )

        self.assertEqual(
            understanding.dependencies,
            tuple(sorted(set(understanding.dependencies))),
        )

    def test_structured_summary_matches_context_counts(self):
        understanding = (
            self.project_context_agent
            .context_understanding
            .understand_task(self._task())
        )

        structured = understanding.structured_summary

        self.assertIsNotNone(structured)

        self.assertEqual(
            structured.relevant_file_count,
            len(understanding.relevant_files),
        )
        self.assertEqual(
            structured.relevant_symbol_count,
            len(understanding.relevant_symbols),
        )
        self.assertEqual(
            structured.relationship_count,
            len(understanding.relationships),
        )
        self.assertEqual(
            structured.dependency_count,
            len(understanding.dependencies),
        )

    def test_agent_service_preserves_complete_context_graph(self):
        execution = self.agent_service.run(
            self._task("task-m1686-agent")
        )

        understanding = execution.context_understanding

        self.assertIsNotNone(understanding)
        self.assertEqual(
            understanding.task.task_id,
            "task-m1686-agent",
        )
        self.assertEqual(
            understanding.relevant_files,
            (Path("main.py"),),
        )
        self.assertEqual(
            understanding.structured_summary.relevant_file_count,
            len(understanding.relevant_files),
        )
        self.assertEqual(
            understanding.structured_summary.relevant_symbol_count,
            len(understanding.relevant_symbols),
        )
        self.assertEqual(
            understanding.structured_summary.relationship_count,
            len(understanding.relationships),
        )
        self.assertEqual(
            understanding.structured_summary.dependency_count,
            len(understanding.dependencies),
        )


if __name__ == "__main__":
    unittest.main()
