
import tempfile
import unittest
from pathlib import Path

from agent_workflow.agent_service import AgentExecution, AgentService
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
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class AgentExecutionClosureM175Tests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        root = Path(self.temp_dir.name)

        (root / "sample.py").write_text(
            "value = 1\n",
            encoding="utf-8",
        )

        scanner = ProjectScanner(root)
        scan_result = scanner.scan()

        project_context = ProjectContextBuilder().build(
            scan_result
        )

        self.project_context_agent = ProjectContextAgentInterface(
            project_context
        )

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

        self.service = AgentService(
            workflow_service,
            project_context_agent=self.project_context_agent,
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def task(self):
        return WorkflowTask(
            task_id="task-m17-5",
            description="M17.5 execution closure",
        )

    def steps(self):
        return (
            WorkflowStep(
                operation="step_1",
                action=lambda: "one",
                step_id="step-001",
            ),
            WorkflowStep(
                operation="step_2",
                action=lambda: "two",
                step_id="step-002",
            ),
        )

    def test_agent_execution_contains_complete_execution_layers(self):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        self.assertIsInstance(
            execution,
            AgentExecution,
        )

        self.assertIsNotNone(execution.run_context)
        self.assertIsNotNone(execution.result)
        self.assertIsNotNone(execution.analysis)
        self.assertIsNotNone(execution.snapshot)
        self.assertIsNotNone(execution.summary)

    def test_task_identity_is_preserved_across_execution(self):
        task = self.task()

        execution = self.service.run(
            task,
            self.steps(),
        )

        self.assertIs(
            execution.task,
            task,
        )

        self.assertEqual(
            execution.task.task_id,
            task.task_id,
        )

        self.assertEqual(
            execution.run_context.task_id,
            task.task_id,
        )

        self.assertEqual(
            execution.context_understanding.task.task_id,
            task.task_id,
        )

    def test_run_id_is_preserved_between_run_context_and_result(self):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        self.assertEqual(
            execution.result.run_id,
            execution.run_context.run_id,
        )

    def test_plan_step_identity_is_preserved_through_execution(self):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        self.assertEqual(
            tuple(
                step.step_id
                for step in execution.plan.steps
            ),
            (
                "step-001",
                "step-002",
            ),
        )

        self.assertEqual(
            tuple(
                step.operation
                for step in execution.plan.steps
            ),
            (
                "step_1",
                "step_2",
            ),
        )

    def test_successful_execution_reaches_completed_result(self):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        self.assertEqual(
            execution.result.status.value,
            "COMPLETED",
        )

        self.assertEqual(
            len(execution.result.step_results),
            2,
        )

        self.assertTrue(
            all(
                item.success
                for item in execution.result.step_results
            )
        )

    def test_context_understanding_remains_observational(self):
        execution = self.service.run(
            self.task(),
            self.steps(),
        )

        self.assertIsInstance(
            execution.context_understanding,
            ContextUnderstandingResult,
        )

        self.assertIsNot(
            execution.context_understanding,
            execution.plan,
        )

        self.assertIsNot(
            execution.context_understanding,
            execution.result,
        )

        self.assertIs(
            execution.project_context_agent,
            self.project_context_agent,
        )

    def test_execution_does_not_mutate_requested_step_sequence(self):
        steps = self.steps()

        original_step_ids = tuple(
            step.step_id
            for step in steps
        )

        original_operations = tuple(
            step.operation
            for step in steps
        )

        execution = self.service.run(
            self.task(),
            steps,
        )

        self.assertEqual(
            tuple(
                step.step_id
                for step in steps
            ),
            original_step_ids,
        )

        self.assertEqual(
            tuple(
                step.operation
                for step in steps
            ),
            original_operations,
        )

        self.assertEqual(
            tuple(
                step.step_id
                for step in execution.plan.steps
            ),
            original_step_ids,
        )

    def test_failed_execution_closes_execution_without_following_actions(self):
        calls = []

        def action_one():
            calls.append("step-001")
            return "one"

        def action_two():
            calls.append("step-002")
            raise RuntimeError("intentional failure")

        def action_three():
            calls.append("step-003")
            return "three"

        steps = (
            WorkflowStep(
                operation="step_1",
                action=action_one,
                step_id="step-001",
            ),
            WorkflowStep(
                operation="step_2",
                action=action_two,
                step_id="step-002",
            ),
            WorkflowStep(
                operation="step_3",
                action=action_three,
                step_id="step-003",
            ),
        )

        execution = self.service.run(
            self.task(),
            steps,
        )

        self.assertEqual(
            calls,
            [
                "step-001",
                "step-002",
            ],
        )

        self.assertEqual(
            execution.result.status.value,
            "FAILED",
        )

        self.assertEqual(
            len(execution.result.step_results),
            2,
        )

        self.assertTrue(
            execution.result.step_results[0].success
        )

        self.assertFalse(
            execution.result.step_results[1].success
        )

        self.assertIsNotNone(execution.snapshot)
        self.assertIsNotNone(execution.summary)


if __name__ == "__main__":
    unittest.main()
