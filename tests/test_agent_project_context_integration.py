import tempfile
import unittest
from pathlib import Path

from agent_workflow.agent_service import AgentService
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
from permissions.reporting import PermissionRiskReport
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class AgentProjectContextIntegrationTests(unittest.TestCase):
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
            "def run():\n    return 'ok'\n",
            encoding="utf-8",
        )

        snapshot_store = SnapshotStore(
            self.project_root,
            self.snapshot_root,
        )

        workflow = AgentWorkflow(
            HistoryStore(self.history_root),
            SnapshotService(
                self.project_root,
                store=snapshot_store,
            ),
            PermissionRiskReport(),
        )

        self.workflow_service = WorkflowService(workflow)

        scan_result = ProjectScanner(self.project_root).scan()
        context = ProjectContextBuilder().build(scan_result)
        self.project_context_agent = ProjectContextAgentInterface(context)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_constructor_accepts_project_context_agent(self) -> None:
        service = AgentService(
            self.workflow_service,
            self.project_context_agent,
        )

        self.assertIs(
            service.project_context_agent,
            self.project_context_agent,
        )

    def test_constructor_rejects_invalid_project_context_agent(self) -> None:
        with self.assertRaises(TypeError):
            AgentService(
                self.workflow_service,
                object(),
            )

    def test_run_carries_project_context_agent(self) -> None:
        service = AgentService(
            self.workflow_service,
            self.project_context_agent,
        )

        task = WorkflowTask(
            task_id="project-context-agent-test",
            description="Run with project context",
        )

        execution = service.run(
            task,
            (
                WorkflowStep(
                    operation="context-test",
                    action=lambda: "ok",
                ),
            ),
        )

        self.assertIs(
            execution.project_context_agent,
            self.project_context_agent,
        )

        self.assertIs(
            execution.project_context_agent.context,
            self.project_context_agent.context,
        )

    def test_agent_can_query_project_files(self) -> None:
        service = AgentService(
            self.workflow_service,
            self.project_context_agent,
        )

        execution = service.run(
            WorkflowTask(
                task_id="query-files-test",
                description="Query project files",
            ),
        )

        project_file = execution.project_context_agent.query.get_file(
            Path("main.py")
        )

        self.assertIsNotNone(project_file)
        self.assertEqual(
            project_file.relative_path,
            Path("main.py"),
        )

    def test_agent_can_query_python_ast(self) -> None:
        service = AgentService(
            self.workflow_service,
            self.project_context_agent,
        )

        execution = service.run(
            WorkflowTask(
                task_id="query-ast-test",
                description="Query Python AST",
            ),
        )

        ast_result = execution.project_context_agent.query.get_python_ast(
            Path("main.py")
        )

        self.assertIsNotNone(ast_result)
        self.assertEqual(
            ast_result.relative_path,
            Path("main.py"),
        )

    def test_agent_can_query_dependencies(self) -> None:
        service = AgentService(
            self.workflow_service,
            self.project_context_agent,
        )

        execution = service.run(
            WorkflowTask(
                task_id="query-dependencies-test",
                description="Query dependencies",
            ),
        )

        targets = (
            execution.project_context_agent.query.dependency_targets(
                Path("main.py")
            )
        )

        self.assertIn("helper", targets)

    def test_agent_can_query_python_file_list(self) -> None:
        service = AgentService(
            self.workflow_service,
            self.project_context_agent,
        )

        execution = service.run(
            WorkflowTask(
                task_id="query-python-files-test",
                description="Query Python files",
            ),
        )

        python_files = execution.project_context_agent.query.python_files()

        self.assertIn(Path("main.py"), python_files)
        self.assertIn(Path("helper.py"), python_files)

    def test_run_produces_context_understanding(self) -> None:
        service = AgentService(
            self.workflow_service,
            self.project_context_agent,
        )

        task = WorkflowTask(
            task_id="context-understanding-test",
            description="Inspect main.py",
            context="target: main.py",
        )

        execution = service.run(task)

        self.assertIsNotNone(execution.context_understanding)
        self.assertIsInstance(
            execution.context_understanding,
            ContextUnderstandingResult,
        )

    def test_context_understanding_preserves_task_identity(self) -> None:
        service = AgentService(
            self.workflow_service,
            self.project_context_agent,
        )

        task = WorkflowTask(
            task_id="context-identity-test",
            project_id="project-identity-test",
            description="Inspect main.py",
            context="target: main.py",
        )

        execution = service.run(task)

        context = execution.context_understanding

        self.assertIsNotNone(context)
        self.assertEqual(
            context.task.task_id,
            task.task_id,
        )
        self.assertEqual(
            context.task.project_id,
            task.project_id,
        )

    def test_context_understanding_selects_target_file(self) -> None:
        service = AgentService(
            self.workflow_service,
            self.project_context_agent,
        )

        task = WorkflowTask(
            task_id="context-target-test",
            description="Inspect main.py",
            context="target: main.py",
        )

        execution = service.run(task)

        context = execution.context_understanding

        self.assertIsNotNone(context)
        self.assertIn(
            Path("main.py"),
            context.relevant_files,
        )

    def test_context_understanding_is_deterministic(self) -> None:
        service = AgentService(
            self.workflow_service,
            self.project_context_agent,
        )

        task = WorkflowTask(
            task_id="context-deterministic-test",
            description="Inspect main.py",
            context="target: main.py",
        )

        first = service.run(task)
        second = service.run(task)

        self.assertEqual(
            first.context_understanding,
            second.context_understanding,
        )

    def test_repeated_runs_do_not_reuse_context_object(self) -> None:
        service = AgentService(
            self.workflow_service,
            self.project_context_agent,
        )

        task_one = WorkflowTask(
            task_id="context-run-one",
            description="Inspect main.py",
            context="target: main.py",
        )

        task_two = WorkflowTask(
            task_id="context-run-two",
            description="Inspect helper.py",
            context="target: helper.py",
        )

        first = service.run(task_one)
        second = service.run(task_two)

        self.assertIsNot(
            first.context_understanding,
            second.context_understanding,
        )

        self.assertEqual(
            first.context_understanding.task.task_id,
            task_one.task_id,
        )
        self.assertEqual(
            second.context_understanding.task.task_id,
            task_two.task_id,
        )

        self.assertIn(
            Path("main.py"),
            first.context_understanding.relevant_files,
        )
        self.assertIn(
            Path("helper.py"),
            second.context_understanding.relevant_files,
        )

    def test_agent_service_without_context_agent_remains_compatible(self) -> None:
        service = AgentService(self.workflow_service)

        task = WorkflowTask(
            task_id="legacy-agent-service-test",
            description="Legacy execution",
        )

        execution = service.run(
            task,
            (
                WorkflowStep(
                    operation="legacy-test",
                    action=lambda: "ok",
                ),
            ),
        )

        self.assertIsNone(execution.project_context_agent)
        self.assertIsNone(execution.context_understanding)
        self.assertEqual(
            execution.result.status.value,
            "COMPLETED",
        )

    def test_context_understanding_does_not_define_run_identity(self) -> None:
        service = AgentService(
            self.workflow_service,
            self.project_context_agent,
        )

        task = WorkflowTask(
            task_id="context-run-identity-test",
            project_id="context-project-test",
            description="Inspect main.py",
            context="target: main.py",
        )

        execution = service.run(task)

        context = execution.context_understanding

        self.assertIsNotNone(context)
        self.assertEqual(
            execution.run_context.run_id,
            execution.result.run_id,
        )
        self.assertNotEqual(
            execution.run_context.run_id,
            context.task.task_id,
        )
        self.assertEqual(
            context.task.project_id,
            task.project_id,
        )


if __name__ == "__main__":
    unittest.main()