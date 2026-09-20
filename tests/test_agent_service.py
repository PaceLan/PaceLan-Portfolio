import tempfile
import unittest
from pathlib import Path

from agent_workflow.agent_service import AgentExecution, AgentService
from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_summary import ExecutionSummary
from agent_workflow.result_analysis import WorkflowResultAnalysis
from agent_workflow.workflow_core import AgentWorkflow, WorkflowStatus, WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_run import WorkflowRunContext
from agent_workflow.workflow_service import WorkflowService
from history.history_core import HistoryStore
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class AgentServiceTests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        history_store = HistoryStore(root / "history.json")
        snapshot_store = SnapshotStore(root, root / "snapshots")
        snapshot_service = SnapshotService(root, store=snapshot_store)

        workflow = AgentWorkflow(
            history_store=history_store,
            snapshot_service=snapshot_service,
        )
        workflow_service = WorkflowService(workflow)
        self.service = AgentService(workflow_service)

    def tearDown(self):
        self.temp_dir.cleanup()

    def task(self):
        return WorkflowTask(
            task_id="task-001",
            description="Run test task",
        )

    def steps(self):
        return (
            WorkflowStep(
                operation="step_1",
                action=lambda: "one",
            ),
            WorkflowStep(
                operation="step_2",
                action=lambda: "two",
            ),
        )

    def test_run_returns_agent_execution(self):
        execution = self.service.run(self.task(), self.steps())
        self.assertIsInstance(execution, AgentExecution)

    def test_run_preserves_task_and_plan(self):
        task = self.task()
        steps = self.steps()
        execution = self.service.run(task, steps)

        self.assertEqual(execution.task, task)
        self.assertIsInstance(execution.plan, WorkflowPlan)
        self.assertEqual(execution.plan.task, task)
        self.assertEqual(
            tuple(step.operation for step in execution.plan.steps),
            ("step_1", "step_2"),
        )

    def test_run_produces_complete_execution_observation(self):
        execution = self.service.run(self.task(), self.steps())

        self.assertIsInstance(execution.run_context, WorkflowRunContext)
        self.assertIsInstance(execution.result, WorkflowResult)
        self.assertIsInstance(execution.analysis, WorkflowResultAnalysis)
        self.assertIsInstance(execution.snapshot, ExecutionSnapshot)
        self.assertIsInstance(execution.summary, ExecutionSummary)

    def test_run_context_matches_snapshot(self):
        execution = self.service.run(self.task(), self.steps())

        self.assertEqual(
            execution.run_context.run_id,
            execution.snapshot.run_id,
        )
        self.assertEqual(
            execution.run_context.task_id,
            execution.snapshot.task_id,
        )

    def test_successful_run_produces_success_result_and_summary(self):
        execution = self.service.run(self.task(), self.steps())

        self.assertEqual(execution.result.status, WorkflowStatus.COMPLETED)
        self.assertTrue(execution.result.completed_successfully)
        self.assertTrue(execution.analysis.is_successful)
        self.assertEqual(execution.summary.successful_steps, 2)
        self.assertEqual(execution.summary.failed_steps, 0)
        self.assertEqual(execution.summary.blocked_steps, 0)

    def test_failure_is_preserved_through_agent_layer(self):
        def fail():
            raise RuntimeError("expected failure")

        steps = (
            WorkflowStep(
                operation="success",
                action=lambda: "ok",
            ),
            WorkflowStep(
                operation="failure",
                action=fail,
            ),
            WorkflowStep(
                operation="skipped",
                action=lambda: "should not run",
            ),
        )

        execution = self.service.run(self.task(), steps)

        self.assertEqual(execution.result.status, WorkflowStatus.FAILED)
        self.assertFalse(execution.result.completed_successfully)
        self.assertTrue(execution.analysis.has_failure)
        self.assertIsNotNone(execution.analysis.first_failed_step)
        self.assertEqual(
            execution.analysis.first_failed_step.operation,
            "failure",
        )
        self.assertEqual(execution.summary.failed_steps, 1)
        self.assertEqual(execution.summary.first_failure, 1)

    def test_repeated_runs_create_independent_executions(self):
        first = self.service.run(self.task(), self.steps())
        second = self.service.run(self.task(), self.steps())

        self.assertNotEqual(
            first.run_context.run_id,
            second.run_context.run_id,
        )
        self.assertNotEqual(
            first.snapshot.run_id,
            second.snapshot.run_id,
        )

    def test_second_run_does_not_reuse_first_run_observation(self):
        first = self.service.run(self.task(), self.steps())
        second = self.service.run(
            self.task(),
            (
                WorkflowStep(
                    operation="only_step",
                    action=lambda: "new",
                ),
            ),
        )

        self.assertEqual(
            tuple(first.snapshot.step_states.keys()),
            ("step-001", "step-002"),
        )
        self.assertEqual(
            tuple(second.snapshot.step_states.keys()),
            ("step-001",),
        )
        self.assertNotEqual(
            first.run_context.run_id,
            second.run_context.run_id,
        )

    def test_run_rejects_invalid_task(self):
        with self.assertRaises(TypeError):
            self.service.run("invalid-task")

    def test_constructor_rejects_invalid_workflow_service(self):
        with self.assertRaises(TypeError):
            AgentService("invalid-workflow-service")

    def test_agent_execution_contains_all_execution_layers(self):
        execution = self.service.run(self.task(), self.steps())

        self.assertIs(execution.task, execution.plan.task)
        self.assertEqual(
            execution.run_context.run_id,
            execution.snapshot.run_id,
        )
        self.assertIsInstance(execution.result, WorkflowResult)
        self.assertIsInstance(execution.analysis, WorkflowResultAnalysis)
        self.assertIsInstance(execution.snapshot, ExecutionSnapshot)
        self.assertIsInstance(execution.summary, ExecutionSummary)

    def test_agent_execution_is_frozen(self):
        execution = self.service.run(self.task(), self.steps())

        with self.assertRaises(AttributeError):
            execution.task = self.task()


if __name__ == "__main__":
    unittest.main()