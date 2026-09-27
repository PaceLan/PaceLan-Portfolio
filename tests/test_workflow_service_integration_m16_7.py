import tempfile
import unittest
from pathlib import Path

from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.workflow_core import AgentWorkflow, WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_service import WorkflowService
from history.history_core import HistoryStore
from snapshots.snapshot_service import SnapshotService


class WorkflowServiceIntegrationM167Tests(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.root = Path(self.temp_dir.name)

        project_root = self.root / "project"
        project_root.mkdir()

        self.history_store = HistoryStore(self.root / "history")
        self.snapshot_service = SnapshotService(project_root)

        self.workflow = AgentWorkflow(
            self.history_store,
            self.snapshot_service,
        )
        self.service = WorkflowService(self.workflow)

    def tearDown(self):
        self.temp_dir.cleanup()

    def make_plan(self, actions):
        task = WorkflowTask(
            task_id="m16-7-task",
            description="M16.7 integration test",
            project_id="m16-7-project",
        )

        steps = tuple(
            WorkflowStep(
                operation=f"operation-{index + 1}",
                action=action,
                step_id=f"step-{index + 1:03d}",
            )
            for index, action in enumerate(actions)
        )

        return WorkflowPlan(task, steps)

    def test_real_success_path_preserves_step_results(self):
        plan = self.make_plan([
            lambda: "result-1",
            lambda: "result-2",
        ])

        result = self.service.execute(plan)

        self.assertIsInstance(result, WorkflowResult)
        self.assertEqual(result.total_steps, 2)
        self.assertEqual(result.successful_steps, 2)
        self.assertEqual(result.failed_steps, 0)
        self.assertTrue(result.completed_successfully)
        self.assertEqual(
            [item.result for item in result.step_results],
            ["result-1", "result-2"],
        )

    def test_real_success_path_has_matching_run_identity(self):
        plan = self.make_plan([lambda: "ok"])

        result = self.service.execute(plan)

        context = self.service.last_run_context
        tracker = self.service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)
        self.assertEqual(result.run_id, context.run_id)
        self.assertEqual(tracker.context.run_id, context.run_id)
        self.assertEqual(tracker.context.task_id, context.task_id)

    def test_real_success_path_completes_tracker(self):
        plan = self.make_plan([
            lambda: "one",
            lambda: "two",
        ])

        result = self.service.execute(plan)
        tracker = self.service.last_execution_tracker

        self.assertTrue(result.completed_successfully)
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

    def test_real_failure_path_preserves_failed_result(self):
        def fail():
            raise RuntimeError("integration failure")

        plan = self.make_plan([
            lambda: "ok",
            fail,
            lambda: "must-not-run",
        ])

        result = self.service.execute(plan)

        self.assertEqual(result.total_steps, 2)
        self.assertEqual(result.successful_steps, 1)
        self.assertEqual(result.failed_steps, 1)
        self.assertFalse(result.completed_successfully)
        self.assertEqual(result.failure_index, 1)
        self.assertEqual(
            [item.operation for item in result.step_results],
            ["operation-1", "operation-2"],
        )

    def test_real_failure_path_fails_tracker_and_skips_remaining(self):
        def fail():
            raise RuntimeError("integration failure")

        plan = self.make_plan([
            lambda: "ok",
            fail,
            lambda: "must-not-run",
        ])

        self.service.execute(plan)
        tracker = self.service.last_execution_tracker

        self.assertIsNotNone(tracker)
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
        self.assertIsNotNone(tracker.finished_at)

    def test_each_real_execution_gets_isolated_identity(self):
        plan1 = self.make_plan([lambda: "first"])

        result1 = self.service.execute(plan1)
        context1 = self.service.last_run_context
        tracker1 = self.service.last_execution_tracker

        task2 = WorkflowTask(
            task_id="m16-7-task-2",
            description="second integration test",
            project_id="m16-7-project",
        )

        plan2 = WorkflowPlan(
            task2,
            (
                WorkflowStep(
                    "operation-second",
                    lambda: "second",
                    step_id="step-001",
                ),
            ),
        )

        result2 = self.service.execute(plan2)
        context2 = self.service.last_run_context
        tracker2 = self.service.last_execution_tracker

        self.assertNotEqual(result1.run_id, result2.run_id)
        self.assertNotEqual(context1.run_id, context2.run_id)
        self.assertIsNot(tracker1, tracker2)
        self.assertEqual(result2.run_id, context2.run_id)
        self.assertEqual(tracker2.context.run_id, context2.run_id)


    def test_blocked_result_fails_tracker_without_running_action(self):
        from permissions.reporting import ApprovalStatus, RiskLevel

        called = []

        def action():
            called.append(True)
            return "must-not-run"

        task = WorkflowTask(
            task_id="m16-7-blocked",
            description="blocked integration test",
            project_id="m16-7-project",
        )

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep(
                    operation="blocked-operation",
                    action=action,
                    risk=RiskLevel.HIGH_RISK,
                    approval=ApprovalStatus.DENIED,
                    step_id="step-001",
                ),
            ),
        )

        result = self.service.execute(plan)
        tracker = self.service.last_execution_tracker

        self.assertEqual(called, [])
        self.assertEqual(result.total_steps, 1)
        self.assertEqual(result.failed_steps, 0)
        self.assertEqual(result.blocked_steps, 1)
        self.assertFalse(result.completed_successfully)
        self.assertIsNotNone(tracker)
        self.assertIs(tracker.run_status, RunStatus.FAILED)

    def test_project_and_task_identity_are_preserved(self):
        plan = self.make_plan([lambda: "ok"])

        result = self.service.execute(plan)
        context = self.service.last_run_context

        self.assertIsNotNone(context)
        self.assertEqual(context.task_id, plan.task.task_id)
        self.assertEqual(plan.task.project_id, "m16-7-project")
        self.assertEqual(result.run_id, context.run_id)

    def test_tracker_snapshot_matches_final_success_state(self):
        plan = self.make_plan([
            lambda: "one",
            lambda: "two",
        ])

        result = self.service.execute(plan)
        tracker = self.service.last_execution_tracker

        snapshot = tracker.snapshot()

        self.assertEqual(snapshot.run_id, result.run_id)
        self.assertEqual(snapshot.task_id, plan.task.task_id)
        self.assertIs(snapshot.run_status, RunStatus.COMPLETED)
        self.assertEqual(
            dict(snapshot.step_states),
            {
                "step-001": StepStatus.SUCCESS,
                "step-002": StepStatus.SUCCESS,
            },
        )
        self.assertIsNone(snapshot.current_step)

    def test_tracker_snapshot_matches_final_failure_state(self):
        def fail():
            raise RuntimeError("snapshot failure")

        plan = self.make_plan([
            lambda: "ok",
            fail,
            lambda: "skip",
        ])

        result = self.service.execute(plan)
        tracker = self.service.last_execution_tracker

        snapshot = tracker.snapshot()

        self.assertEqual(snapshot.run_id, result.run_id)
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

    def test_execution_does_not_leak_previous_tracker_state(self):
        plan1 = self.make_plan([
            lambda: "first",
            lambda: "second",
        ])

        self.service.execute(plan1)
        tracker1 = self.service.last_execution_tracker

        task2 = WorkflowTask(
            task_id="m16-7-isolated",
            description="isolated execution",
            project_id="m16-7-project",
        )

        plan2 = WorkflowPlan(
            task2,
            (
                WorkflowStep(
                    operation="new-operation",
                    action=lambda: "new",
                    step_id="step-001",
                ),
            ),
        )

        self.service.execute(plan2)
        tracker2 = self.service.last_execution_tracker

        self.assertIsNot(tracker1, tracker2)
        self.assertEqual(
            dict(tracker2.step_states),
            {"step-001": StepStatus.SUCCESS},
        )
        self.assertNotIn("step-002", tracker2.step_states)

    def test_empty_plan_has_consistent_run_identity(self):
        plan = self.make_plan([])

        result = self.service.execute(plan)
        context = self.service.last_run_context
        tracker = self.service.last_execution_tracker

        self.assertIsNotNone(context)
        self.assertIsNotNone(tracker)
        self.assertEqual(result.run_id, context.run_id)
        self.assertEqual(tracker.context.run_id, context.run_id)
        self.assertEqual(result.total_steps, 0)

    def test_legacy_empty_step_ids_are_normalized_before_execution(self):
        task = WorkflowTask(
            task_id="m16-7-legacy",
            description="legacy step identity",
            project_id="m16-7-project",
        )

        plan = WorkflowPlan(
            task,
            (
                WorkflowStep(
                    operation="legacy-one",
                    action=lambda: "one",
                ),
                WorkflowStep(
                    operation="legacy-two",
                    action=lambda: "two",
                ),
            ),
        )

        result = self.service.execute(plan)
        tracker = self.service.last_execution_tracker

        self.assertEqual(result.total_steps, 2)
        self.assertEqual(
            tuple(tracker.step_states.keys()),
            ("step-001", "step-002"),
        )

    def test_success_execution_is_deterministic_for_same_actions(self):
        task1 = WorkflowTask(
            task_id="m16-7-deterministic-1",
            description="deterministic test",
            project_id="project-a",
        )
        task2 = WorkflowTask(
            task_id="m16-7-deterministic-2",
            description="deterministic test",
            project_id="project-a",
        )

        plan1 = WorkflowPlan(
            task1,
            (
                WorkflowStep(
                    operation="same-operation",
                    action=lambda: "same-result",
                    step_id="step-001",
                ),
            ),
        )
        plan2 = WorkflowPlan(
            task2,
            (
                WorkflowStep(
                    operation="same-operation",
                    action=lambda: "same-result",
                    step_id="step-001",
                ),
            ),
        )

        result1 = self.service.execute(plan1)
        result2 = self.service.execute(plan2)

        self.assertEqual(
            [(r.operation, r.status, r.result, r.success)
             for r in result1.step_results],
            [(r.operation, r.status, r.result, r.success)
             for r in result2.step_results],
        )
        self.assertNotEqual(result1.run_id, result2.run_id)

    def test_invalid_plan_does_not_replace_previous_run_state(self):
        valid_plan = self.make_plan([lambda: "ok"])

        self.service.execute(valid_plan)

        previous_context = self.service.last_run_context
        previous_tracker = self.service.last_execution_tracker

        with self.assertRaises((TypeError, ValueError)):
            self.service.execute("not-a-workflow-plan")

        self.assertIs(self.service.last_run_context, previous_context)
        self.assertIs(self.service.last_execution_tracker, previous_tracker)

    def test_failure_does_not_execute_remaining_actions(self):
        calls = []

        def first():
            calls.append("first")
            return "first"

        def second():
            calls.append("second")
            raise RuntimeError("failure")

        def third():
            calls.append("third")
            return "must-not-run"

        plan = self.make_plan([first, second, third])

        self.service.execute(plan)

        self.assertEqual(calls, ["first", "second"])

    def test_each_execution_creates_a_new_run_context(self):
        plan = self.make_plan([lambda: "first"])

        self.service.execute(plan)
        context1 = self.service.last_run_context

        self.service.execute(plan)
        context2 = self.service.last_run_context

        self.assertIsNot(context1, context2)
        self.assertNotEqual(context1.run_id, context2.run_id)
        self.assertEqual(context1.task_id, context2.task_id)
