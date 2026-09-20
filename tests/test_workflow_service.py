import unittest
from unittest.mock import MagicMock, patch

from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.plan_builder import build_plan
from agent_workflow.workflow_core import AgentWorkflow, WorkflowStatus, WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_run import WorkflowRunContext
from agent_workflow.workflow_service import WorkflowService
from agent_workflow.workflow_outcome import (
    is_blocked,
    is_failed,
    is_success,
)


class WorkflowServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.history_store = MagicMock()
        self.snapshot_service = MagicMock()
        self.workflow = AgentWorkflow(
            history_store=self.history_store,
            snapshot_service=self.snapshot_service,
        )
        self.service = WorkflowService(self.workflow)

    def test_service_creation(self) -> None:
        self.assertIs(self.service.workflow, self.workflow)
        self.assertIsNone(self.service.last_run_context)
        self.assertIsNone(self.service.last_execution_tracker)

    def test_invalid_workflow_type_rejected(self) -> None:
        with self.assertRaises(TypeError):
            WorkflowService(object())  # type: ignore[arg-type]

    def test_valid_plan_runs(self) -> None:
        task = WorkflowTask("task-1", "Run test workflow")
        calls: list[str] = []

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep(
                    "step-1",
                    lambda: calls.append("step-1") or "ok-1",
                ),
                WorkflowStep(
                    "step-2",
                    lambda: calls.append("step-2") or "ok-2",
                ),
            ),
        )

        result = self.service.execute(plan)

        self.assertEqual(calls, ["step-1", "step-2"])
        self.assertEqual(result.total_steps, 2)
        self.assertEqual(result.successful_steps, 2)
        self.assertTrue(result.completed_successfully)

    def test_execute_normalizes_legacy_empty_step_ids(self) -> None:
        task = WorkflowTask("task-legacy", "Legacy plan test")
        calls: list[str] = []

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep(
                    "legacy-step",
                    lambda: calls.append("legacy-step") or "done",
                ),
            ),
        )

        self.assertEqual(plan.steps[0].step_id, "")

        result = self.service.execute(plan)

        self.assertEqual(calls, ["legacy-step"])
        self.assertEqual(result.total_steps, 1)
        self.assertEqual(result.successful_steps, 1)

        tracker = self.service.last_execution_tracker
        self.assertIsNotNone(tracker)
        self.assertEqual(
            tuple(tracker.snapshot().step_states.keys()),
            ("step-001",),
        )

    def test_run_context_is_established_from_plan_task(self) -> None:
        task = WorkflowTask("task-context", "Context test")
        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step", lambda: "done"),
            ),
        )

        self.service.execute(plan)

        context = self.service.last_run_context
        self.assertIsInstance(context, WorkflowRunContext)
        self.assertEqual(context.task_id, task.task_id)
        self.assertIsInstance(context.run_id, str)
        self.assertTrue(context.run_id)

    def test_execution_tracker_is_established_from_run_context(self) -> None:
        task = WorkflowTask("task-tracker", "Tracker test")
        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step-1", lambda: "done"),
                WorkflowStep("step-2", lambda: "done"),
            ),
        )

        self.service.execute(plan)

        context = self.service.last_run_context
        tracker = self.service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)
        self.assertIs(tracker.context, context)
        self.assertEqual(
            tracker.snapshot().run_status,
            RunStatus.COMPLETED,
        )
        self.assertEqual(
            tuple(tracker.snapshot().step_states.keys()),
            ("step-001", "step-002"),
        )

    def test_result_identity_matches_run_context(self) -> None:
        task = WorkflowTask(
            "task-result-identity",
            "Result identity test",
        )
        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step", lambda: "done"),
            ),
        )

        result = self.service.execute(plan)

        context = self.service.last_run_context
        self.assertIsNotNone(context)

        self.assertEqual(result.run_id, context.run_id)

    def test_successful_execution_tracks_complete_state(self) -> None:
        task = WorkflowTask("task-state-success", "State success test")
        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step-1", lambda: "one"),
                WorkflowStep("step-2", lambda: "two"),
            ),
        )

        result = self.service.execute(plan)

        tracker = self.service.last_execution_tracker
        self.assertIsNotNone(tracker)

        self.assertIs(tracker.run_status, RunStatus.COMPLETED)
        self.assertEqual(
            dict(tracker.step_states),
            {
                "step-001": StepStatus.SUCCESS,
                "step-002": StepStatus.SUCCESS,
            },
        )
        self.assertIsNone(tracker.current_step)
        self.assertIsNotNone(tracker.started_at)
        self.assertIsNotNone(tracker.finished_at)
        self.assertGreaterEqual(
            tracker.finished_at,
            tracker.started_at,
        )

        snapshot = tracker.snapshot()

        self.assertIs(snapshot.run_status, tracker.run_status)
        self.assertEqual(
            dict(snapshot.step_states),
            dict(tracker.step_states),
        )
        self.assertEqual(
            snapshot.current_step,
            tracker.current_step,
        )
        self.assertEqual(
            snapshot.started_at,
            tracker.started_at,
        )
        self.assertEqual(
            snapshot.finished_at,
            tracker.finished_at,
        )
        self.assertEqual(result.status, WorkflowStatus.COMPLETED)

    def test_failed_execution_tracks_skipped_remaining_steps(self) -> None:
        task = WorkflowTask("task-state-failure", "State failure test")
        calls: list[str] = []

        def fail() -> str:
            calls.append("failure")
            raise RuntimeError("expected failure")

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep(
                    "step-1",
                    lambda: calls.append("step-1") or "one",
                ),
                WorkflowStep("step-2", fail),
                WorkflowStep(
                    "step-3",
                    lambda: calls.append("step-3") or "three",
                ),
            ),
        )

        result = self.service.execute(plan)

        tracker = self.service.last_execution_tracker
        self.assertIsNotNone(tracker)

        self.assertEqual(
            calls,
            ["step-1", "failure"],
        )

        self.assertIs(tracker.run_status, RunStatus.FAILED)
        self.assertEqual(
            dict(tracker.step_states),
            {
                "step-001": StepStatus.SUCCESS,
                "step-002": StepStatus.FAILED,
                "step-003": StepStatus.SKIPPED,
            },
        )
        self.assertIsNone(tracker.current_step)
        self.assertIsNotNone(tracker.started_at)
        self.assertIsNotNone(tracker.finished_at)
        self.assertGreaterEqual(
            tracker.finished_at,
            tracker.started_at,
        )

        snapshot = tracker.snapshot()

        self.assertIs(snapshot.run_status, RunStatus.FAILED)
        self.assertEqual(
            dict(snapshot.step_states),
            {
                "step-001": StepStatus.SUCCESS,
                "step-002": StepStatus.FAILED,
                "step-003": StepStatus.SKIPPED,
            },
        )
        self.assertIsNone(snapshot.current_step)

        self.assertEqual(result.status, WorkflowStatus.FAILED)
        self.assertEqual(len(result.step_results), 2)

    def test_result_and_tracker_terminal_states_match(self) -> None:
        success_task = WorkflowTask(
            "task-result-success",
            "Result success test",
        )
        success_plan = WorkflowPlan(
            success_task,
            (
                WorkflowStep("step", lambda: "done"),
            ),
        )

        success_result = self.service.execute(success_plan)
        success_tracker = self.service.last_execution_tracker

        self.assertIsNotNone(success_tracker)
        self.assertEqual(
            success_result.status,
            WorkflowStatus.COMPLETED,
        )
        self.assertIs(
            success_tracker.run_status,
            RunStatus.COMPLETED,
        )

        failure_task = WorkflowTask(
            "task-result-failure",
            "Result failure test",
        )

        def fail() -> str:
            raise RuntimeError("expected failure")

        failure_plan = WorkflowPlan(
            failure_task,
            (
                WorkflowStep("step", fail),
            ),
        )

        failure_result = self.service.execute(failure_plan)
        failure_tracker = self.service.last_execution_tracker

        self.assertIsNotNone(failure_tracker)
        self.assertEqual(
            failure_result.status,
            WorkflowStatus.FAILED,
        )
        self.assertIs(
            failure_tracker.run_status,
            RunStatus.FAILED,
        )

    def test_each_execution_gets_a_new_execution_tracker(self) -> None:
        task = WorkflowTask("task-multiple", "Multiple runs")
        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step", lambda: "done"),
            ),
        )

        self.service.execute(plan)
        first_tracker = self.service.last_execution_tracker
        first_context = self.service.last_run_context

        self.service.execute(plan)
        second_tracker = self.service.last_execution_tracker
        second_context = self.service.last_run_context

        self.assertIsNot(first_tracker, second_tracker)
        self.assertIsNot(first_context, second_context)
        self.assertIs(first_tracker.context, first_context)
        self.assertIs(second_tracker.context, second_context)

    def test_invalid_plan_does_not_create_execution_tracker(self) -> None:
        invalid_plan = object()

        with self.assertRaises(TypeError):
            self.service.execute(invalid_plan)  # type: ignore[arg-type]

        self.assertIsNone(self.service.last_run_context)
        self.assertIsNone(self.service.last_execution_tracker)

    def test_successful_step_is_recorded(self) -> None:
        task = WorkflowTask("task-record", "Record test")
        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step", lambda: "done"),
            ),
        )

        result = self.service.execute(plan)

        self.assertEqual(len(result.step_results), 1)
        step_result = result.step_results[0]
        self.assertTrue(step_result.success)
        self.assertEqual(step_result.status, WorkflowStatus.COMPLETED)
        self.assertEqual(step_result.result, "done")

    def test_steps_execute_in_plan_order(self) -> None:
        task = WorkflowTask("task-order", "Order test")
        calls: list[str] = []

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("first", lambda: calls.append("first") or "1"),
                WorkflowStep("second", lambda: calls.append("second") or "2"),
                WorkflowStep("third", lambda: calls.append("third") or "3"),
            ),
        )

        result = self.service.execute(plan)

        self.assertEqual(calls, ["first", "second", "third"])
        self.assertEqual(result.successful_steps, 3)

    def test_all_successful_produces_success_result(self) -> None:
        task = WorkflowTask("task-success", "Success test")
        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step-1", lambda: "1"),
                WorkflowStep("step-2", lambda: "2"),
            ),
        )

        result = self.service.execute(plan)

        self.assertEqual(result.status, WorkflowStatus.COMPLETED)
        self.assertTrue(result.completed_successfully)
        self.assertTrue(is_success(result))
        self.assertFalse(is_failed(result))
        self.assertFalse(is_blocked(result))

    def test_step_failure_produces_failed_result(self) -> None:
        task = WorkflowTask("task-failure", "Failure test")

        def fail() -> str:
            raise RuntimeError("expected test failure")

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step-1", fail),
            ),
        )

        result = self.service.execute(plan)

        self.assertEqual(result.status, WorkflowStatus.FAILED)
        self.assertEqual(result.failed_steps, 1)
        self.assertFalse(result.completed_successfully)
        self.assertTrue(is_failed(result))

    def test_failure_stops_later_steps(self) -> None:
        task = WorkflowTask("task-stop", "Stop test")
        calls: list[str] = []

        def fail() -> str:
            calls.append("failed")
            raise RuntimeError("stop")

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("first", lambda: calls.append("first") or "1"),
                WorkflowStep("failure", fail),
                WorkflowStep("later", lambda: calls.append("later") or "3"),
            ),
        )

        result = self.service.execute(plan)

        self.assertEqual(calls, ["first", "failed"])
        self.assertEqual(len(result.step_results), 2)
        self.assertEqual(result.failure_index, 1)

    def test_executed_results_are_preserved(self) -> None:
        task = WorkflowTask("task-preserve", "Preservation test")

        def fail() -> str:
            raise ValueError("expected")

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("success", lambda: "preserved"),
                WorkflowStep("failure", fail),
            ),
        )

        result = self.service.execute(plan)

        self.assertEqual(len(result.step_results), 2)
        self.assertEqual(result.step_results[0].result, "preserved")
        self.assertTrue(result.step_results[0].success)
        self.assertFalse(result.step_results[1].success)

    def test_invalid_plan_is_rejected_before_execution(self) -> None:
        invalid_plan = object()

        with self.assertRaises(TypeError):
            self.service.execute(invalid_plan)  # type: ignore[arg-type]

        self.assertIsNone(self.service.last_run_context)
        self.assertIsNone(self.service.last_execution_tracker)

    def test_result_type_is_workflow_result(self) -> None:
        task = WorkflowTask("task-type", "Type test")
        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step", lambda: "done"),
            ),
        )

        result = self.service.execute(plan)

        self.assertIsInstance(result, WorkflowResult)

    def test_outcome_helpers_match_result(self) -> None:
        task = WorkflowTask("task-outcome", "Outcome test")

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step", lambda: "done"),
            ),
        )

        result = self.service.execute(plan)

        self.assertEqual(result.status, WorkflowStatus.COMPLETED)
        self.assertEqual(is_success(result), result.completed_successfully)

    def test_service_routes_execution_through_workflow_layer(self) -> None:
        task = WorkflowTask("task-boundary", "Boundary test")
        plan = WorkflowPlan(
            task,
            (
                WorkflowStep("step", lambda: "done"),
            ),
        )

        expected_result = MagicMock()
        expected_result.success = True

        with patch(
            "agent_workflow.workflow_service.run_plan",
            return_value=(expected_result,),
        ) as mocked_run_plan:
            with patch.object(
                WorkflowResult,
                "from_step_results",
                return_value=MagicMock(spec=WorkflowResult),
            ) as mocked_result:
                self.service.execute(plan)

        normalized_plan = build_plan(
            plan.task,
            plan.steps,
        )

        mocked_run_plan.assert_called_once_with(
            self.workflow,
            normalized_plan,
            self.service.last_execution_tracker,
        )

        context = self.service.last_run_context
        self.assertIsNotNone(context)

        mocked_result.assert_called_once_with(
            (expected_result,),
            run_id=context.run_id,
        )


if __name__ == "__main__":
    unittest.main()