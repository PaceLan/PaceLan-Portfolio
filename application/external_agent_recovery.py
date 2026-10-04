from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from application.external_agent import (
    ExternalAgentRequest,
    ExternalAgentStatus,
    ExternalConnectionReason,
    ExternalConnectionState,
)
from application.external_agent_gateway import ExternalAgentGateway
from application.restore_service import RestoreService
from application.universal_agent_interface import (
    AgentTaskStatus,
    UniversalAgentInterface,
)


class ExternalRecoveryState(str, Enum):
    NOT_FOUND = "not_found"
    PERSISTED_ONLY = "persisted_only"
    READY = "ready"
    RECONNECTED = "reconnected"
    RESUMED = "resumed"


@dataclass(frozen=True)
class ExternalRecoveryResult:
    state: ExternalRecoveryState
    task_id: str
    workflow_id: str | None
    project_id: str | None
    run_id: str | None
    task_status: str | None
    run_status: str | None
    recoverable: bool
    message: str = ""


class ExternalAgentRecoveryService:
    """Restores external-session state without fabricating runtime state."""

    def __init__(
        self,
        gateway: ExternalAgentGateway,
        restore_service: RestoreService | None = None,
    ) -> None:
        self._gateway = gateway
        self._restore = restore_service or RestoreService()

    def mark_connection_lost(
        self,
        *,
        message: str = "",
    ) -> ExternalAgentStatus:
        return self._gateway.wait_external(
            ExternalConnectionReason.CONNECTION_LOST,
            message=message,
            recoverable=True,
        )

    def inspect_persisted(
        self,
        project_path: str | Path,
        request: ExternalAgentRequest,
    ) -> ExternalRecoveryResult:
        if not self._restore.has_project(project_path):
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.NOT_FOUND,
                task_id=request.task_id,
                workflow_id=request.workflow_id,
                project_id=None,
                run_id=None,
                task_status=None,
                run_status=None,
                recoverable=False,
                message="no persisted project exists",
            )

        restored = self._restore.restore(project_path)
        workflow = restored.workflow

        if workflow is None:
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.NOT_FOUND,
                task_id=request.task_id,
                workflow_id=request.workflow_id,
                project_id=restored.project.project_id,
                run_id=None,
                task_status=None,
                run_status=None,
                recoverable=False,
                message="no persisted workflow exists",
            )

        if workflow.task.task_id != request.task_id:
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.NOT_FOUND,
                task_id=request.task_id,
                workflow_id=request.workflow_id,
                project_id=restored.project.project_id,
                run_id=workflow.run.run_id,
                task_status=None,
                run_status=workflow.snapshot.run_status,
                recoverable=False,
                message="persisted workflow belongs to another task",
            )

        run_status = workflow.snapshot.run_status
        recoverable = run_status in {
            "RUNNING",
            "PAUSED",
            "WAITING_EXTERNAL",
        }

        return ExternalRecoveryResult(
            state=(
                ExternalRecoveryState.READY
                if recoverable
                else ExternalRecoveryState.PERSISTED_ONLY
            ),
            task_id=workflow.task.task_id,
            workflow_id=request.workflow_id,
            project_id=workflow.task.project_id,
            run_id=workflow.run.run_id,
            task_status=None,
            run_status=run_status,
            recoverable=recoverable,
            message=(
                "persisted workflow is eligible for recovery"
                if recoverable
                else "persisted workflow is not in a recoverable runtime state"
            ),
        )

    def reconnect(
        self,
        project_path: str | Path,
        request: ExternalAgentRequest,
    ) -> ExternalRecoveryResult:
        persisted = self.inspect_persisted(project_path, request)

        if not persisted.recoverable:
            return persisted

        self._gateway.connect()

        try:
            task = self._gateway.inspect_task(request)
        except (KeyError, RuntimeError):
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.PERSISTED_ONLY,
                task_id=persisted.task_id,
                workflow_id=persisted.workflow_id,
                project_id=persisted.project_id,
                run_id=persisted.run_id,
                task_status=None,
                run_status=persisted.run_status,
                recoverable=True,
                message=(
                    "persisted workflow is recoverable, "
                    "but the in-memory Agent task is not present"
                ),
            )

        return ExternalRecoveryResult(
            state=ExternalRecoveryState.RECONNECTED,
            task_id=persisted.task_id,
            workflow_id=persisted.workflow_id,
            project_id=persisted.project_id,
            run_id=persisted.run_id,
            task_status=task.status.value,
            run_status=persisted.run_status,
            recoverable=task.status in {
                AgentTaskStatus.PAUSED,
                AgentTaskStatus.RUNNING,
            },
            message="external session reconnected to the live Agent task",
        )

    def resume(
        self,
        project_path: str | Path,
        request: ExternalAgentRequest,
    ) -> ExternalRecoveryResult:
        reconnected = self.reconnect(project_path, request)

        if reconnected.state is not ExternalRecoveryState.RECONNECTED:
            return reconnected

        if reconnected.task_status != AgentTaskStatus.PAUSED.value:
            return reconnected

        runtime = self._gateway.resume(request)

        return ExternalRecoveryResult(
            state=ExternalRecoveryState.RESUMED,
            task_id=reconnected.task_id,
            workflow_id=reconnected.workflow_id,
            project_id=reconnected.project_id,
            run_id=reconnected.run_id,
            task_status=AgentTaskStatus.RUNNING.value,
            run_status=reconnected.run_status,
            recoverable=True,
            message=(
                "original in-memory Agent task resumed"
                if runtime.accepted
                else runtime.message
            ),
        )


__all__ = [
    "ExternalAgentRecoveryService",
    "ExternalRecoveryResult",
    "ExternalRecoveryState",
]
