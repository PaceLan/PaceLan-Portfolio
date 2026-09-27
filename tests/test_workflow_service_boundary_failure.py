import unittest
from unittest.mock import MagicMock, patch

from agent_workflow.execution_tracking import RunStatus
from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.plan_builder import build_plan
from agent_workflow.workflow_core import AgentWorkflow, WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_run import WorkflowRunContext
from agent_workflow.workflow_service import WorkflowService


class WorkflowServiceBoundaryFailureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.history_store = MagicMock()
        self.snapshot_service = MagicMock()
        self.workflow = AgentWorkflow(
            history_store=self.history_store,
            snapshot_service=self.snapshot_service,
        )
        self.service = WorkflowService(self.workflow)

    def _plan(self) -> WorkflowPlan:
        task = WorkflowTask(
            "task-boundary",
            "boundary failure isolation",
        )
        step = WorkflowStep(
            "step-001",
            lambda: "done",
        )
        return WorkflowPlan(task, (step,))

    def test_plan_validation_failure_does_not_create_run_state(self):
        plan = self._plan()

        with patch(
            "agent_workflow.workflow_service.build_plan",
            side_effect=ValueError("invalid plan"),
        ):
            with self.assertRaises(ValueError):
                self.service.execute(plan)

        self.assertIsNone(self.service.last_run_context)
        self.assertIsNone(self.service.last_execution_tracker)

    def test_context_creation_failure_does_not_create_tracker(self):
        plan = self._plan()

        with patch(
            "agent_workflow.workflow_service.WorkflowRunContext.create",
            side_effect=RuntimeError("context creation failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.service.execute(plan)

        self.assertIsNone(self.service.last_run_context)
        self.assertIsNone(self.service.last_execution_tracker)

    def test_tracker_creation_failure_preserves_established_context(self):
        plan = self._plan()

        with patch(
            "agent_workflow.workflow_service.ExecutionTracker",
            side_effect=RuntimeError("tracker creation failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.service.execute(plan)

        context = self.service.last_run_context

        self.assertIsNotNone(context)
        self.assertIsInstance(context, WorkflowRunContext)
        self.assertIsNone(self.service.last_execution_tracker)

    def test_tracker_start_failure_preserves_context_and_tracker(self):
        plan = self._plan()

        with patch.object(
            # The real tracker instance is created normally; only start_run
            # is forced to fail at the service boundary.
            ExecutionTracker,
            "start_run",
            side_effect=RuntimeError("tracker start failure"),
        ):
            with self.assertRaises(RuntimeError):
                self.service.execute(plan)

        context = self.service.last_run_context
        tracker = self.service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)
        self.assertIs(tracker.context, context)
        self.assertEqual(
            tracker.run_status,
            RunStatus.CREATED,
        )

    def test_result_construction_failure_preserves_context_and_tracker(self):
        plan = self._plan()
        expected_step_result = MagicMock()

        with patch(
            "agent_workflow.workflow_service.run_plan",
            return_value=(expected_step_result,),
        ) as mocked_run_plan:
            with patch.object(
                WorkflowResult,
                "from_step_results",
                side_effect=RuntimeError("result construction failure"),
            ):
                with self.assertRaises(RuntimeError):
                    self.service.execute(plan)

        context = self.service.last_run_context
        tracker = self.service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)
        self.assertIs(tracker.context, context)

        normalized_plan = build_plan(
            plan.task,
            plan.steps,
        )

        mocked_run_plan.assert_called_once_with(
            self.workflow,
            normalized_plan,
            tracker,
        )

        self.assertEqual(
            tracker.context.run_id,
            context.run_id,
        )


if __name__ == "__main__":
    unittest.main()
