"""Small deterministic foundation for future Agent Workflow integration."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, Optional

from history.history_core import HistoryEntry, HistoryStore
from permissions.reporting import (
    ApprovalStatus,
    OperationRecord,
    PermissionRiskReport,
    RiskLevel,
)
from snapshots.snapshot_service import SnapshotService


class WorkflowStatus(str, Enum):
    """Lifecycle states for a workflow task or step."""

    RECEIVED = "RECEIVED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class WorkflowTask:
    """Immutable context established when a task enters the workflow."""

    task_id: str
    description: str
    context: str = ""
    project_id: str = ""


@dataclass(frozen=True)
class WorkflowStepResult:
    """Outcome of one explicitly submitted workflow action."""

    operation: str
    status: WorkflowStatus
    result: str
    success: bool


class AgentWorkflow:
    """Coordinate explicit actions across reporting, history, and snapshots."""

    def __init__(
        self,
        history_store: HistoryStore,
        snapshot_service: SnapshotService,
        report: Optional[PermissionRiskReport] = None,
    ) -> None:
        self.history_store = history_store
        self.snapshot_service = snapshot_service
        self.report = report or PermissionRiskReport()
        self._task_status: Dict[str, WorkflowStatus] = {}

    def start_task(self, task: WorkflowTask) -> WorkflowTask:
        """Register a task as received without executing any action."""
        if not task.task_id:
            raise ValueError("Workflow task ID must not be empty")
        if task.task_id in self._task_status:
            raise ValueError(f"Workflow task already exists: {task.task_id}")
        self._task_status[task.task_id] = WorkflowStatus.RECEIVED
        return task

    def task_status(self, task_id: str) -> WorkflowStatus:
        """Return the current status of a registered task."""
        try:
            return self._task_status[task_id]
        except KeyError as error:
            raise KeyError(f"Unknown workflow task: {task_id}") from error

    def run_step(
        self,
        task: WorkflowTask,
        operation: str,
        action: Callable[[], str],
        *,
        risk: RiskLevel = RiskLevel.SAFE,
        approval: ApprovalStatus = ApprovalStatus.NOT_REQUESTED,
        target: str = ".",
        context: Optional[str] = None,
    ) -> WorkflowStepResult:
        """Evaluate and execute one explicit action callback.

        Permission records are classification only. DENIED and BLOCKED actions
        are not called; other statuses are passed through unchanged.
        """
        self._require_task(task)
        self._task_status[task.task_id] = WorkflowStatus.IN_PROGRESS
        self.report.add(OperationRecord(operation, risk, approval, context))

        if approval in {ApprovalStatus.DENIED, ApprovalStatus.BLOCKED}:
            result = WorkflowStepResult(
                operation,
                WorkflowStatus.BLOCKED,
                approval.value,
                False,
            )
            self._record_history(operation, target, result.result, False)
            self._task_status[task.task_id] = WorkflowStatus.BLOCKED
            return result

        try:
            action_result = str(action())
        except Exception as error:
            result = WorkflowStepResult(
                operation,
                WorkflowStatus.FAILED,
                type(error).__name__,
                False,
            )
            self._record_history(operation, target, result.result, False)
            self._task_status[task.task_id] = WorkflowStatus.FAILED
            return result

        result = WorkflowStepResult(
            operation,
            WorkflowStatus.COMPLETED,
            action_result,
            True,
        )
        self._record_history(operation, target, result.result, True)
        self._task_status[task.task_id] = WorkflowStatus.COMPLETED
        return result

    def create_snapshot(
        self,
        task: WorkflowTask,
        *,
        risk: RiskLevel = RiskLevel.NOTABLE,
        approval: ApprovalStatus = ApprovalStatus.NOT_REQUESTED,
    ) -> Optional[str]:
        """Explicitly create a snapshot after classification."""
        result = self.run_step(
            task,
            "create snapshot",
            lambda: self.snapshot_service.create_snapshot().snapshot_id,
            risk=risk,
            approval=approval,
            target=".",
            context="explicit snapshot request",
        )
        return result.result if result.success else None

    def restore_snapshot(
        self,
        task: WorkflowTask,
        snapshot_id: str,
        *,
        overwrite: bool = False,
        risk: RiskLevel = RiskLevel.HIGH_RISK,
        approval: ApprovalStatus = ApprovalStatus.NOT_REQUESTED,
    ) -> WorkflowStepResult:
        """Explicitly restore a snapshot through SnapshotService safety checks."""
        return self.run_step(
            task,
            "restore snapshot",
            lambda: self.snapshot_service.restore_snapshot(
                snapshot_id,
                overwrite=overwrite,
            ).snapshot_id,
            risk=risk,
            approval=approval,
            target=snapshot_id,
            context="explicit snapshot restore request",
        )

    def complete_task(self, task: WorkflowTask) -> WorkflowStatus:
        """Mark a task complete only when its current status is successful."""
        self._require_task(task)
        if self._task_status[task.task_id] is not WorkflowStatus.COMPLETED:
            raise ValueError("Workflow task has no successful completed step")
        return self._task_status[task.task_id]

    def render_report(self, rollback: str = "Not recommended") -> str:
        """Render the current deterministic Permission/Risk report."""
        return self.report.render(rollback)

    def _require_task(self, task: WorkflowTask) -> None:
        if task.task_id not in self._task_status:
            raise KeyError(f"Unknown workflow task: {task.task_id}")

    def _record_history(
        self,
        operation: str,
        target: str,
        result: str,
        success: bool,
    ) -> None:
        entry = HistoryEntry(
            timestamp=datetime.now(timezone.utc).isoformat(),
            operation=operation,
            target=target,
            result=result,
            success=success,
        )
        try:
            self.history_store.append(entry)
        except Exception:
            pass