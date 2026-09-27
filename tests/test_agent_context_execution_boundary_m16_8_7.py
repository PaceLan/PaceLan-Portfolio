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
from agent_workflow.workflow_plan import WorkflowStep
from agent_workflow.workflow_service import WorkflowService
from history.history_core import HistoryStore
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class AgentContextExecutionBoundaryM1687Tests(unittest.TestCase):
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

        self.project_context_agent = ProjectContextAgentInterface(context)

        self.agent_service = AgentService(
            self.workflow_service,
            project_context_agent=self.project_context_agent,
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def _task(self, task_id: str = "task-m1687") -> WorkflowTask:
        return WorkflowTask(
            task_id=task_id,
            project_id="project-m1687",
            description="inspect project",
        )

    def test_context_and_execution_result_coexist(self) -> None:
        execution = self.agent_service.run(self._task())

        self.assertIsNotNone(execution.context_understanding)
        self.assertIsNotNone(execution.result)
        self.assertIsNotNone(execution.snapshot)
        self.assertIsNotNone(execution.summary)

    def test_context_identity_matches_execution_task(self) -> None:
        task = self._task()

        execution = self.agent_service.run(task)
        context = execution.context_understanding

        self.assertIsNotNone(context)
        self.assertEqual(context.task.task_id, task.task_id)
        self.assertEqual(context.task.project_id, task.project_id)
        self.assertEqual(execution.task.task_id, task.task_id)
        self.assertEqual(execution.task.project_id, task.project_id)

    def test_run_identity_is_preserved(self) -> None:
        execution = self.agent_service.run(self._task())

        self.assertEqual(
            execution.result.run_id,
            execution.run_context.run_id,
        )
        self.assertTrue(execution.result.run_id)

    def test_context_does_not_define_run_identity(self) -> None:
        execution = self.agent_service.run(self._task())

        context = execution.context_understanding

        self.assertIsNotNone(context)
        self.assertFalse(hasattr(context, "run_id"))
        self.assertEqual(
            context.task.task_id,
            execution.task.task_id,
        )
        self.assertEqual(
            context.task.project_id,
            execution.task.project_id,
        )

    def test_summary_matches_result_and_snapshot(self) -> None:
        execution = self.agent_service.run(self._task())

        expected = execution.summary.__class__.from_result_and_snapshot(
            execution.result,
            execution.snapshot,
        )

        self.assertEqual(execution.summary, expected)

    def test_successful_execution_retains_context(self) -> None:
        execution = self.agent_service.run(self._task())

        self.assertIsNotNone(execution.context_understanding)
        self.assertIsNotNone(execution.result)

    def test_failed_execution_retains_context(self) -> None:
        def fail() -> str:
            raise RuntimeError("m1687 controlled failure")

        failing_step = WorkflowStep(
            "failure",
            fail,
            target="main.py",
        )

        execution = self.agent_service.run(
            self._task("task-m1687-failure"),
            steps=(failing_step,),
        )

        self.assertIsNotNone(execution.context_understanding)
        self.assertIsNotNone(execution.result)
        self.assertIsNotNone(execution.snapshot)
        self.assertIsNotNone(execution.summary)

        self.assertFalse(execution.result.completed_successfully)
        self.assertGreater(execution.result.failed_steps, 0)

        self.assertEqual(
            execution.context_understanding.task.task_id,
            execution.task.task_id,
        )
        self.assertEqual(
            execution.context_understanding.task.project_id,
            execution.task.project_id,
        )


    def test_context_and_run_identity_remain_independent(self) -> None:
        execution = self.agent_service.run(self._task())

        self.assertEqual(
            execution.context_understanding.task.task_id,
            execution.task.task_id,
        )
        self.assertEqual(
            execution.result.run_id,
            execution.run_context.run_id,
        )
        self.assertNotEqual(
            execution.context_understanding.task.task_id,
            execution.result.run_id,
        )


if __name__ == "__main__":
    unittest.main()