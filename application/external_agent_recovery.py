from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from time import sleep
from typing import Callable

from application.external_agent import (
    ExternalAgentRequest,
    ExternalAgentStatus,
    ExternalConnectionReason,
    ExternalConnectionState,
)
from application.external_agent_gateway import ExternalAgentGateway
from application.external_agent_session import (
    ExternalAgentSessionCapability,
    ExternalAgentSessionState,
)
from application.restore_service import RestoreService
from application.recovery_state_storage import RecoveryStateStorage
from application.external_agent_retry_policy import (
    ExternalAgentRetryDecision,
    ExternalAgentRetryPolicy,
)
from application.universal_agent_interface import (
    AgentTaskStatus,
    UniversalAgentInterface,
)


class ExternalRecoveryState(str, Enum):
    NOT_FOUND = "not_found"
    PERSISTED_ONLY = "persisted_only"
    SESSION_NOT_AVAILABLE = "session_not_available"
    SESSION_ATTACHED = "session_attached"
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


@dataclass(frozen=True)
class ExternalAgentRecoveryContext:
    """Persisted Agent context required to continue the original work."""

    project_id: str
    goal: str
    task: object
    plan: object
    run: object
    execution: object
    result: object
    verification: object | None
    context: object | None
    error: str | None


class ExternalAgentRecoveryService:
    """Restores external-session state without fabricating runtime state."""

    def __init__(
        self,
        gateway: ExternalAgentGateway,
        restore_service: RestoreService | None = None,
        retry_policy: ExternalAgentRetryPolicy | None = None,
        sleeper: Callable[[float], None] = sleep,
        session_capability: ExternalAgentSessionCapability | None = None,
    ) -> None:
        self._gateway = gateway
        self._restore = restore_service or RestoreService()
        self._retry_policy = retry_policy or ExternalAgentRetryPolicy()
        self._sleeper = sleeper
        self._session_capability = session_capability

    @staticmethod
    def verify_continuity(
        request: ExternalAgentRequest,
        result: ExternalRecoveryResult,
    ) -> bool:
        """Verify that recovery still refers to the original execution chain."""
        if result.task_id != request.task_id:
            return False
        if result.workflow_id != request.workflow_id:
            return False
        return True

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

    def restore_agent_context(
        self,
        project_path: str | Path,
        request: ExternalAgentRequest,
    ) -> ExternalAgentRecoveryContext | None:
        """Restore persisted context required to continue the original Task."""
        restored = self._restore.restore(project_path)
        workflow = restored.workflow

        if workflow is None or workflow.task.task_id != request.task_id:
            return None

        recovery_state = RecoveryStateStorage(project_path).load()
        error = recovery_state.reason if recovery_state is not None else None
        if error == "":
            error = None

        return ExternalAgentRecoveryContext(
            project_id=restored.project.project_id,
            goal=restored.project.goal.text,
            task=workflow.task,
            plan=workflow.plan,
            run=workflow.run,
            execution=workflow.snapshot,
            result=workflow.result,
            verification=workflow.verification,
            context=restored.context,
            error=error,
        )

    def recover_existing_session(
        self,
        project_path: str | Path,
        request: ExternalAgentRequest,
        session_id: str | None,
    ) -> ExternalRecoveryResult:
        """Reuse a verified existing external session; never create a replacement."""
        persisted = self.inspect_persisted(project_path, request)

        if not persisted.recoverable:
            return persisted

        if not session_id:
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.SESSION_NOT_AVAILABLE,
                task_id=persisted.task_id,
                workflow_id=persisted.workflow_id,
                project_id=persisted.project_id,
                run_id=persisted.run_id,
                task_status=None,
                run_status=persisted.run_status,
                recoverable=True,
                message="no persisted external Agent session is available",
            )

        capability = self._session_capability
        if capability is None:
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.SESSION_NOT_AVAILABLE,
                task_id=persisted.task_id,
                workflow_id=persisted.workflow_id,
                project_id=persisted.project_id,
                run_id=persisted.run_id,
                task_status=None,
                run_status=persisted.run_status,
                recoverable=True,
                message="external Agent provider does not expose Session recovery",
            )

        try:
            inspected = capability.inspect_session(session_id, request)
        except (KeyError, RuntimeError, ValueError):
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.SESSION_NOT_AVAILABLE,
                task_id=persisted.task_id,
                workflow_id=persisted.workflow_id,
                project_id=persisted.project_id,
                run_id=persisted.run_id,
                task_status=None,
                run_status=persisted.run_status,
                recoverable=True,
                message="persisted external Agent Session could not be verified",
            )

        if inspected.session_id != session_id:
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.SESSION_NOT_AVAILABLE,
                task_id=persisted.task_id,
                workflow_id=persisted.workflow_id,
                project_id=persisted.project_id,
                run_id=persisted.run_id,
                task_status=None,
                run_status=persisted.run_status,
                recoverable=True,
                message="external Agent Session identity does not match persisted state",
            )

        if inspected.state is ExternalAgentSessionState.UNAVAILABLE:
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.SESSION_NOT_AVAILABLE,
                task_id=persisted.task_id,
                workflow_id=persisted.workflow_id,
                project_id=persisted.project_id,
                run_id=persisted.run_id,
                task_status=None,
                run_status=persisted.run_status,
                recoverable=True,
                message=inspected.message or "existing external Agent Session is unavailable",
            )

        try:
            attached = capability.attach_session(session_id, request)
        except (KeyError, RuntimeError, ValueError):
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.SESSION_NOT_AVAILABLE,
                task_id=persisted.task_id,
                workflow_id=persisted.workflow_id,
                project_id=persisted.project_id,
                run_id=persisted.run_id,
                task_status=None,
                run_status=persisted.run_status,
                recoverable=True,
                message="existing external Agent Session could not be attached",
            )

        if attached.session_id != session_id:
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.SESSION_NOT_AVAILABLE,
                task_id=persisted.task_id,
                workflow_id=persisted.workflow_id,
                project_id=persisted.project_id,
                run_id=persisted.run_id,
                task_status=None,
                run_status=persisted.run_status,
                recoverable=True,
                message="attached external Agent Session identity does not match persisted state",
            )

        result = ExternalRecoveryResult(
            state=ExternalRecoveryState.SESSION_ATTACHED,
            task_id=persisted.task_id,
            workflow_id=persisted.workflow_id,
            project_id=persisted.project_id,
            run_id=persisted.run_id,
            task_status=None,
            run_status=persisted.run_status,
            recoverable=True,
            message="existing external Agent Session was verified and attached",
        )
        if not self.verify_continuity(request, result):
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.PERSISTED_ONLY,
                task_id=result.task_id,
                workflow_id=result.workflow_id,
                project_id=result.project_id,
                run_id=result.run_id,
                task_status=result.task_status,
                run_status=result.run_status,
                recoverable=False,
                message="recovered external Agent identity does not match original task workflow",
            )
        return result

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

    def recover(
        self,
        project_path: str | Path,
        request: ExternalAgentRequest,
    ) -> ExternalRecoveryResult:
        """Perform Level 1 silent recovery without creating new runtime state."""
        persisted = self.inspect_persisted(project_path, request)

        if not persisted.recoverable:
            return persisted

        attempt = 0
        connected = self._gateway.status()

        if connected.state is ExternalConnectionState.WAITING_EXTERNAL:
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
                    connected.message
                    or "external Agent recovery is waiting for external availability"
                ),
            )

        while connected.state is not ExternalConnectionState.CONNECTED:
            decision = self._retry_policy.decide(attempt=attempt)

            if decision.decision is ExternalAgentRetryDecision.STOP:
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
                        connected.message
                        or decision.message
                    ),
                )

            if attempt > 0 and decision.delay_seconds > 0:
                self._sleeper(decision.delay_seconds)

            connected = self._gateway.connect()

            if connected.state is ExternalConnectionState.CONNECTED:
                break

            attempt += 1

            if self._retry_policy.decide(
                attempt=attempt,
            ).decision is ExternalAgentRetryDecision.STOP:
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
                        connected.message
                        or "external Agent connection retry limit reached"
                    ),
                )

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
                    "but the original Agent task is not present"
                ),
            )

        task_status = task.status.value

        if task.status is AgentTaskStatus.RUNNING:
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.RECONNECTED,
                task_id=persisted.task_id,
                workflow_id=persisted.workflow_id,
                project_id=persisted.project_id,
                run_id=persisted.run_id,
                task_status=task_status,
                run_status=persisted.run_status,
                recoverable=True,
                message="original running Agent task is already connected",
            )

        if task.status is not AgentTaskStatus.PAUSED:
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.PERSISTED_ONLY,
                task_id=persisted.task_id,
                workflow_id=persisted.workflow_id,
                project_id=persisted.project_id,
                run_id=persisted.run_id,
                task_status=task_status,
                run_status=persisted.run_status,
                recoverable=False,
                message=(
                    "original Agent task is not in a silently recoverable state"
                ),
            )

        runtime = self._gateway.resume(request)

        if not runtime.accepted:
            return ExternalRecoveryResult(
                state=ExternalRecoveryState.RECONNECTED,
                task_id=persisted.task_id,
                workflow_id=persisted.workflow_id,
                project_id=persisted.project_id,
                run_id=persisted.run_id,
                task_status=task_status,
                run_status=persisted.run_status,
                recoverable=True,
                message=runtime.message or "Agent task resume was not accepted",
            )

        return ExternalRecoveryResult(
            state=ExternalRecoveryState.RESUMED,
            task_id=persisted.task_id,
            workflow_id=persisted.workflow_id,
            project_id=persisted.project_id,
            run_id=persisted.run_id,
            task_status=AgentTaskStatus.RUNNING.value,
            run_status=persisted.run_status,
            recoverable=True,
            message="original paused Agent task silently recovered and resumed",
        )


__all__ = [
    "ExternalAgentRecoveryContext",
    "ExternalAgentRecoveryService",
    "ExternalRecoveryResult",
    "ExternalRecoveryState",
]
