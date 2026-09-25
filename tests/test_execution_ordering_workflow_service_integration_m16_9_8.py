import tempfile
import unittest

from agent_workflow.execution_ordering import ExecutionOrdering
from agent_workflow.workflow_core import AgentWorkflow, WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from agent_workflow.workflow_service import WorkflowService
from history.history_core import HistoryStore
from snapshots.snapshot_service import SnapshotService
from permissions.reporting import ApprovalStatus, RiskLevel


class ExecutionOrderingWorkflowServiceIntegrationM1698Tests(
    unittest.TestCase
):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        self.workflow = AgentWorkflow(
            history_store=HistoryStore(self.temp_dir.name),
            snapshot_service=SnapshotService(self.temp_dir.name),
        )
        self.service = WorkflowService(self.workflow)
        self.ordering = ExecutionOrdering()

    def _task(self):
        return WorkflowTask(
            task_id="task-m1698",
            project_id="project-m1698",
            description="execution ordering service integration",
        )

    def _step(
        self,
        step_id,
        calls,
        *,
        risk=RiskLevel.SAFE,
        approval=ApprovalStatus.NOT_REQUESTED,
    ):
        def action():
            calls.append(step_id)
            return step_id

        return WorkflowStep(
            operation="execute",
            action=action,
            risk=risk,
            approval=approval,
            step_id=step_id,
        )

    def test_ordered_plan_executes_in_dependency_order(self):
        calls = []

        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step("step-003", calls),
                self._step("step-001", calls),
                self._step("step-002", calls),
            ),
        )

        ordered = self.ordering.order(
            plan,
            {
                "step-002": ("step-001",),
                "step-003": ("step-002",),
            },
        )

        result = self.service.execute(ordered)

        self.assertTrue(result.completed_successfully)
        self.assertEqual(
            calls,
            ["step-001", "step-002", "step-003"],
        )

    def test_ordering_failure_prevents_service_execution(self):
        calls = []

        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step("step-001", calls),
                self._step("step-002", calls),
            ),
        )

        with self.assertRaises(ValueError):
            self.ordering.order(
                plan,
                {
                    "step-001": ("step-002",),
                    "step-002": ("step-001",),
                },
            )

        self.assertEqual(calls, [])

    def test_ordering_does_not_execute_actions(self):
        calls = []

        plan = WorkflowPlan(
            task=self._task(),
            steps=(
                self._step("step-002", calls),
                self._step("step-001", calls),
            ),
        )

        ordered = self.ordering.order(
            plan,
            {
                "step-002": ("step-001",),
            },
        )

        self.assertEqual(calls, [])
        self.assertEqual(
            tuple(step.step_id for step in ordered.steps),
            ("step-001", "step-002"),
        )

    def test_ordering_preserves_task_and_step_identity(self):
        calls = []

        step1 = self._step("step-001", calls)
        step2 = self._step("step-002", calls)

        plan = WorkflowPlan(
            task=self._task(),
            steps=(step2, step1),
        )

        ordered = self.ordering.order(
            plan,
            {
                "step-002": ("step-001",),
            },
        )

        self.assertIs(ordered.task, plan.task)
        self.assertIs(ordered.steps[0], step1)
        self.assertIs(ordered.steps[1], step2)
        self.assertIsNot(ordered, plan)

    def test_ordering_then_service_is_deterministic(self):
        def make_plan(calls):
            return WorkflowPlan(
                task=self._task(),
                steps=(
                    self._step("step-003", calls),
                    self._step("step-001", calls),
                    self._step("step-002", calls),
                ),
            )

        calls1 = []
        calls2 = []

        dependencies = {
            "step-002": ("step-001",),
            "step-003": ("step-002",),
        }

        ordered1 = self.ordering.order(
            make_plan(calls1),
            dependencies,
        )
        ordered2 = self.ordering.order(
            make_plan(calls2),
            dependencies,
        )

        result1 = self.service.execute(ordered1)
        result2 = self.service.execute(ordered2)

        self.assertTrue(result1.completed_successfully)
        self.assertTrue(result2.completed_successfully)
        self.assertEqual(calls1, calls2)
        self.assertEqual(
            calls1,
            ["step-001", "step-002", "step-003"],
        )


if __name__ == "__main__":
    unittest.main()
