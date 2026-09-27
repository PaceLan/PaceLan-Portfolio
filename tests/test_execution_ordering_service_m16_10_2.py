import tempfile
import unittest
from pathlib import Path

from agent_workflow.workflow_core import AgentWorkflow
from agent_workflow.execution_ordering import ExecutionOrdering
from agent_workflow.execution_readiness import ExecutionReadiness
from history.history_core import HistoryStore
from snapshots.snapshot_service import SnapshotService
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from agent_workflow.workflow_service import WorkflowService


class TestExecutionOrderingServiceM1610(unittest.TestCase):

    def setUp(self):
        self._history_temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._history_temporary_directory.cleanup)

    def _service(self):
        history = HistoryStore(self._history_temporary_directory.name)
        snapshots = SnapshotService(
            self._history_temporary_directory.name,
        )
        workflow = AgentWorkflow(
            history_store=history,
            snapshot_service=snapshots,
        )
        return WorkflowService(workflow)

    def test_ordered_plan_executes_in_dependency_order(self):
        calls = []

        def action_one():
            calls.append("step-001")
            return "one"

        def action_two():
            calls.append("step-002")
            return "two"

        def action_three():
            calls.append("step-003")
            return "three"

        task = WorkflowTask(
            task_id="task-order",
            description="dependency ordering",
        )

        step_one = WorkflowStep(
            operation="one",
            action=action_one,
            step_id="step-001",
        )
        step_two = WorkflowStep(
            operation="two",
            action=action_two,
            step_id="step-002",
        )
        step_three = WorkflowStep(
            operation="three",
            action=action_three,
            step_id="step-003",
        )

        plan = WorkflowPlan(
            task=task,
            steps=(step_three, step_one, step_two),
        )

        ordered = ExecutionOrdering().order(
            plan,
            {
                "step-001": (),
                "step-002": ("step-001",),
                "step-003": ("step-002",),
            },
        )

        readiness = ExecutionReadiness().check(ordered)
        self.assertTrue(readiness.ready)
        self.assertEqual(
            tuple(step.step_id for step in ordered.steps),
            ("step-001", "step-002", "step-003"),
        )

        result = self._service().execute(ordered)

        self.assertEqual(
            calls,
            ["step-001", "step-002", "step-003"],
        )
        self.assertEqual(len(result.step_results), 3)
        self.assertTrue(all(item.success for item in result.step_results))

    def test_service_preserves_ordered_plan_step_sequence(self):
        calls = []

        def make_action(step_id):
            def action():
                calls.append(step_id)
                return step_id

            return action

        task = WorkflowTask(
            task_id="task-preserve",
            description="preserve ordered plan",
        )

        steps = tuple(
            WorkflowStep(
                operation=step_id,
                action=make_action(step_id),
                step_id=step_id,
            )
            for step_id in (
                "step-001",
                "step-002",
                "step-003",
            )
        )

        plan = WorkflowPlan(task=task, steps=steps)

        service = self._service()
        result = service.execute(plan)

        self.assertEqual(
            calls,
            ["step-001", "step-002", "step-003"],
        )
        self.assertEqual(len(result.step_results), 3)
        self.assertTrue(all(item.success for item in result.step_results))

    def test_failed_step_stops_following_execution(self):
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

        task = WorkflowTask(
            task_id="task-failure",
            description="stop after failure",
        )

        plan = WorkflowPlan(
            task=task,
            steps=(
                WorkflowStep(
                    operation="one",
                    action=action_one,
                    step_id="step-001",
                ),
                WorkflowStep(
                    operation="two",
                    action=action_two,
                    step_id="step-002",
                ),
                WorkflowStep(
                    operation="three",
                    action=action_three,
                    step_id="step-003",
                ),
            ),
        )

        result = self._service().execute(plan)

        self.assertEqual(
            calls,
            ["step-001", "step-002"],
        )
        self.assertEqual(len(result.step_results), 2)
        self.assertTrue(result.step_results[0].success)
        self.assertFalse(result.step_results[1].success)


if __name__ == "__main__":
    unittest.main()



