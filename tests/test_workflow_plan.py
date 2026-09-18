import tempfile
import unittest
from pathlib import Path

from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.workflow_core import AgentWorkflow, WorkflowStatus, WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep, run_plan
from agent_workflow.workflow_run import WorkflowRunContext
from history.history_core import HistoryStore
from permissions.reporting import ApprovalStatus, PermissionRiskReport, RiskLevel
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class WorkflowPlanTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.project_root = root / "project"
        self.snapshot_root = root / "snapshots"
        self.history_root = root / "history"

        self.project_root.mkdir()
        self.history_root.mkdir()
        (self.project_root / "main.py").write_text(
            "print('baseline')\n",
            encoding="utf-8",
        )

        snapshot_store = SnapshotStore(
            self.project_root,
            self.snapshot_root,
        )

        self.workflow = AgentWorkflow(
            HistoryStore(self.history_root),
            SnapshotService(
                self.project_root,
                store=snapshot_store,
            ),
            PermissionRiskReport(),
        )

        self.task = WorkflowTask(
            "plan-task-1",
            "execute structured plan",
            "plan test context",
        )

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def make_tracker(self, plan: WorkflowPlan) -> ExecutionTracker:
        context = WorkflowRunContext.create(plan.task)
        tracker = ExecutionTracker(
            context,
            tuple(step.operation for step in plan.steps),
        )
        tracker.start_run()
        return tracker

    def test_successful_plan_executes_steps_in_order(self) -> None:
        executed = []

        plan = WorkflowPlan(
            self.task,
            (
                WorkflowStep(
                    "step one",
                    lambda: executed.append("one") or "one complete",
                ),
                WorkflowStep(
                    "step two",
                    lambda: executed.append("two") or "two complete",
                ),
            ),
        )

        tracker = self.make_tracker(plan)
        results = run_plan(self.workflow, plan, tracker)

        self.assertEqual(executed, ["one", "two"])
        self.assertEqual(len(results), 2)
        self.assertEqual(
            [result.status for result in results],
            [
                WorkflowStatus.COMPLETED,
                WorkflowStatus.COMPLETED,
            ],
        )
        self.assertEqual(
            self.workflow.task_status(self.task.task_id),
            WorkflowStatus.COMPLETED,
        )
        self.assertEqual(
            tracker.run_status.value,
            "COMPLETED",
        )
        self.assertEqual(
            len(self.workflow.history_store.read_history()),
            2,
        )

    def test_denied_step_stops_plan_without_executing_it_or_later_steps(
        self,
    ) -> None:
        executed = []

        plan = WorkflowPlan(
            self.task,
            (
                WorkflowStep(
                    "safe step",
                    lambda: executed.append("safe") or "done",
                ),
                WorkflowStep(
                    "denied step",
                    lambda: executed.append("denied") or "should not run",
                    risk=RiskLevel.HIGH_RISK,
                    approval=ApprovalStatus.DENIED,
                ),
                WorkflowStep(
                    "after denied",
                    lambda: executed.append("after") or "should not run",
                ),
            ),
        )

        tracker = self.make_tracker(plan)
        results = run_plan(self.workflow, plan, tracker)

        self.assertEqual(executed, ["safe"])
        self.assertEqual(len(results), 2)
        self.assertEqual(results[-1].status, WorkflowStatus.BLOCKED)
        self.assertFalse(results[-1].success)
        self.assertEqual(
            self.workflow.task_status(self.task.task_id),
            WorkflowStatus.BLOCKED,
        )
        self.assertEqual(
            tracker.run_status.value,
            "FAILED",
        )

    def test_blocked_step_stops_plan_without_executing_it(self) -> None:
        executed = []

        plan = WorkflowPlan(
            self.task,
            (
                WorkflowStep(
                    "blocked step",
                    lambda: executed.append(True) or "should not run",
                    approval=ApprovalStatus.BLOCKED,
                ),
                WorkflowStep(
                    "after blocked",
                    lambda: executed.append("after") or "should not run",
                ),
            ),
        )

        tracker = self.make_tracker(plan)
        results = run_plan(self.workflow, plan, tracker)

        self.assertEqual(executed, [])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, WorkflowStatus.BLOCKED)

    def test_exception_stops_plan_and_records_failure(self) -> None:
        executed = []

        def failing_action() -> str:
            executed.append("failing")
            raise RuntimeError("controlled failure")

        plan = WorkflowPlan(
            self.task,
            (
                WorkflowStep("failing step", failing_action),
                WorkflowStep(
                    "after failure",
                    lambda: executed.append("after") or "should not run",
                ),
            ),
        )

        tracker = self.make_tracker(plan)
        results = run_plan(self.workflow, plan, tracker)

        self.assertEqual(executed, ["failing"])
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].status, WorkflowStatus.FAILED)
        self.assertFalse(results[0].success)
        self.assertEqual(
            self.workflow.task_status(self.task.task_id),
            WorkflowStatus.FAILED,
        )
        self.assertEqual(
            tracker.run_status.value,
            "FAILED",
        )

        history = self.workflow.history_store.read_history()
        self.assertEqual(len(history), 1)
        self.assertFalse(history[0].success)

    def test_step_risk_and_approval_are_forwarded(self) -> None:
        plan = WorkflowPlan(
            self.task,
            (
                WorkflowStep(
                    "reviewable step",
                    lambda: "approved",
                    risk=RiskLevel.NOTABLE,
                    approval=ApprovalStatus.APPROVED,
                    target="src",
                    context="structured plan test",
                ),
            ),
        )

        tracker = self.make_tracker(plan)
        results = run_plan(self.workflow, plan, tracker)

        self.assertEqual(results[0].status, WorkflowStatus.COMPLETED)

        report = self.workflow.render_report()
        self.assertIn("reviewable step", report)
        self.assertIn("Approved / notable operations", report)
        self.assertIn("APPROVED", report)

    def test_empty_plan_is_deterministic(self) -> None:
        plan = WorkflowPlan(self.task, ())

        tracker = self.make_tracker(plan)
        results = run_plan(self.workflow, plan, tracker)

        self.assertEqual(results, ())
        self.assertEqual(
            self.workflow.task_status(self.task.task_id),
            WorkflowStatus.RECEIVED,
        )
        self.assertEqual(
            self.workflow.history_store.read_history(),
            [],
        )
        self.assertEqual(
            tracker.run_status.value,
            "COMPLETED",
        )


if __name__ == "__main__":
    unittest.main()