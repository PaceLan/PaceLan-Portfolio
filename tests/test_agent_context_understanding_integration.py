import tempfile
import unittest
from pathlib import Path

from agent_workflow.agent_service import AgentExecution, AgentService
from agent_workflow.context_understanding import (
    ContextSummary,
    ContextUnderstandingResult,
)
from agent_workflow.project_context import ProjectContextBuilder
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.project_scanner import ProjectScanner
from agent_workflow.workflow_core import (
    AgentWorkflow,
    WorkflowTask,
)
from agent_workflow.workflow_service import WorkflowService
from history.history_core import HistoryStore
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class AgentContextUnderstandingIntegrationTests(unittest.TestCase):

    def _build_context(self, root: Path):
        scanner = ProjectScanner(root)
        scan_result = scanner.scan()
        return ProjectContextBuilder().build(scan_result)

    def _build_agent_service(
        self,
        root: Path,
        project_context_agent=None,
    ):
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

        return AgentService(
            workflow_service,
            project_context_agent=project_context_agent,
        )

    def _task(self, description="update target: main.py"):
        return WorkflowTask(
            task_id="task-context-001",
            project_id="project-001",
            description=description,
            context="",
        )

    def test_interface_exposes_context_understanding(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            (root / "main.py").write_text(
                "class Main:\n    pass\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            interface = ProjectContextAgentInterface(context)

            self.assertIsNotNone(
                interface.context_understanding
            )

    def test_context_understanding_returns_structured_summary(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            (root / "main.py").write_text(
                "class Main:\n    pass\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            interface = ProjectContextAgentInterface(context)

            result = (
                interface.context_understanding
                .understand_task(self._task())
            )

            self.assertIsInstance(
                result,
                ContextUnderstandingResult,
            )
            self.assertIsInstance(
                result.structured_summary,
                ContextSummary,
            )

            summary = result.structured_summary

            self.assertEqual(
                summary.task_id,
                "task-context-001",
            )
            self.assertEqual(
                summary.project_id,
                "project-001",
            )
            self.assertEqual(
                summary.target,
                "main.py",
            )

    def test_structured_summary_matches_result(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            (root / "main.py").write_text(
                "class Main:\n    pass\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            interface = ProjectContextAgentInterface(context)

            result = (
                interface.context_understanding
                .understand_task(self._task())
            )

            summary = result.structured_summary

            self.assertEqual(
                summary.relevant_file_count,
                len(result.relevant_files),
            )
            self.assertEqual(
                summary.relevant_symbol_count,
                len(result.relevant_symbols),
            )
            self.assertEqual(
                summary.relationship_count,
                len(result.relationships),
            )
            self.assertEqual(
                summary.dependency_count,
                len(result.dependencies),
            )

    def test_context_understanding_is_deterministic(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            (root / "main.py").write_text(
                "class Main:\n    pass\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            interface = ProjectContextAgentInterface(context)

            first = (
                interface.context_understanding
                .understand_task(self._task())
            )
            second = (
                interface.context_understanding
                .understand_task(self._task())
            )

            self.assertEqual(first, second)

    def test_symbol_relationship_association_is_precise(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            (root / "main.py").write_text(
                "class Main:\n"
                "    pass\n\n"
                "def helper():\n"
                "    pass\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            interface = ProjectContextAgentInterface(context)

            result = (
                interface.context_understanding
                .understand_task(self._task())
            )

            symbol_names = {
                symbol.name
                for symbol in result.relevant_symbols
            }

            contains_targets = {
                relationship.target
                for relationship in result.relationships
                if relationship.kind == "contains"
            }

            self.assertTrue(
                contains_targets.issubset(symbol_names)
            )

    def test_agent_service_includes_context_understanding(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            (root / "main.py").write_text(
                "class Main:\n"
                "    pass\n",
                encoding="utf-8",
            )

            context = self._build_context(root)
            interface = ProjectContextAgentInterface(context)

            service = self._build_agent_service(
                root,
                project_context_agent=interface,
            )

            execution = service.run(self._task())

            self.assertIsInstance(
                execution,
                AgentExecution,
            )
            self.assertIsNotNone(
                execution.context_understanding
            )
            self.assertEqual(
                execution.context_understanding.task.task_id,
                "task-context-001",
            )

    def test_agent_service_without_context_agent_remains_compatible(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)

            service = self._build_agent_service(root)

            execution = service.run(self._task())

            self.assertIsInstance(
                execution,
                AgentExecution,
            )
            self.assertIsNone(
                execution.context_understanding
            )


if __name__ == "__main__":
    unittest.main()