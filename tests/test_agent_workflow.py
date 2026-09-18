import tempfile
import unittest
from pathlib import Path

from agent_workflow.workflow_core import (
    AgentWorkflow,
    WorkflowStatus,
    WorkflowTask,
)
from history.history_core import HistoryStore
from permissions.reporting import ApprovalStatus, PermissionRiskReport, RiskLevel
from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class AgentWorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.project_root = root / "project"
        self.snapshot_root = root / "snapshots"
        self.history_root = root / "history"
        self.project_root.mkdir()
        self.history_root.mkdir()
        (self.project_root / "main.py").write_text("print('baseline')\n", encoding="utf-8")
        snapshot_store = SnapshotStore(self.project_root, self.snapshot_root)
        self.workflow = AgentWorkflow(
            HistoryStore(self.history_root),
            SnapshotService(self.project_root, store=snapshot_store),
        )
        self.task = WorkflowTask("task-1", "validate the project", "test context")

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_task_context_and_status_are_deterministic(self) -> None:
        self.assertEqual(self.workflow.start_task(self.task), self.task)
        self.assertEqual(self.workflow.task_status("task-1"), WorkflowStatus.RECEIVED)

    def test_successful_step_updates_history_and_report(self) -> None:
        self.workflow.start_task(self.task)

        result = self.workflow.run_step(
            self.task,
            "inspect project",
            lambda: "completed",
            risk=RiskLevel.SAFE,
            approval=ApprovalStatus.NOT_REQUESTED,
            target=".",
        )

        self.assertEqual(result.status, WorkflowStatus.COMPLETED)
        self.assertTrue(result.success)
        self.assertEqual(self.workflow.task_status("task-1"), WorkflowStatus.COMPLETED)
        self.assertEqual(len(self.workflow.history_store.read_history()), 1)
        self.assertIn("inspect project", self.workflow.render_report())

    def test_denied_step_is_not_executed(self) -> None:
        self.workflow.start_task(self.task)
        executed = []

        result = self.workflow.run_step(
            self.task,
            "dangerous action",
            lambda: executed.append(True),
            risk=RiskLevel.HIGH_RISK,
            approval=ApprovalStatus.DENIED,
        )

        self.assertEqual(result.status, WorkflowStatus.BLOCKED)
        self.assertFalse(result.success)
        self.assertEqual(executed, [])
        self.assertEqual(self.workflow.task_status("task-1"), WorkflowStatus.BLOCKED)
        self.assertIn("DENIED", self.workflow.render_report())

    def test_failed_step_records_failure_without_raising(self) -> None:
        self.workflow.start_task(self.task)

        result = self.workflow.run_step(
            self.task,
            "failing action",
            lambda: (_ for _ in ()).throw(RuntimeError("controlled failure")),
        )

        self.assertEqual(result.status, WorkflowStatus.FAILED)
        self.assertFalse(result.success)
        self.assertEqual(result.result, "RuntimeError")
        self.assertFalse(self.workflow.history_store.read_history()[0].success)

    def test_snapshot_operations_delegate_explicitly(self) -> None:
        self.workflow.start_task(self.task)

        snapshot_id = self.workflow.create_snapshot(
            self.task,
            approval=ApprovalStatus.APPROVED,
        )

        self.assertIsNotNone(snapshot_id)
        self.assertEqual(len(self.workflow.snapshot_service.list_snapshots()), 1)
        self.assertEqual(self.workflow.history_store.read_history()[0].operation, "create snapshot")

    def test_restore_requires_approval_and_preserves_snapshot_safety(self) -> None:
        self.workflow.start_task(self.task)
        snapshot_id = self.workflow.create_snapshot(self.task, approval=ApprovalStatus.APPROVED)
        target = self.project_root / "main.py"
        target.write_text("changed\n", encoding="utf-8")

        blocked = self.workflow.restore_snapshot(
            self.task,
            snapshot_id,
            overwrite=True,
            approval=ApprovalStatus.BLOCKED,
        )

        self.assertEqual(blocked.status, WorkflowStatus.BLOCKED)
        self.assertEqual(target.read_text(encoding="utf-8"), "changed\n")

    def test_history_failure_does_not_change_action_result(self) -> None:
        class FailingHistoryStore:
            def append(self, entry) -> None:
                raise OSError("history unavailable")

        workflow = AgentWorkflow(
            FailingHistoryStore(),
            self.workflow.snapshot_service,
            PermissionRiskReport(),
        )
        workflow.start_task(self.task)

        result = workflow.run_step(self.task, "safe action", lambda: "still completed")

        self.assertTrue(result.success)
        self.assertEqual(result.status, WorkflowStatus.COMPLETED)


if __name__ == "__main__":
    unittest.main()
