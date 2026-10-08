from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from application.external_agent import ExternalAgentRequest
from application.external_agent_recovery import (
    ExternalRecoveryResult,
    ExternalRecoveryState,
    ExternalAgentRecoveryService,
)


class RecoveryContinuationState(str, Enum):
    CONTINUED = "CONTINUED"
    NOT_READY = "NOT_READY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class RecoveryContinuationResult:
    state: RecoveryContinuationState
    task_id: str
    workflow_id: str | None
    run_id: str | None
    message: str

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")


class ExternalAgentRecoveryContinuationService:
    """Continue the original execution chain after verified recovery."""

    def continue_original(
        self,
        request: ExternalAgentRequest,
        recovery: ExternalRecoveryResult,
    ) -> RecoveryContinuationResult:
        if not isinstance(request, ExternalAgentRequest):
            raise TypeError("request must be an ExternalAgentRequest")
        if not isinstance(recovery, ExternalRecoveryResult):
            raise TypeError("recovery must be an ExternalRecoveryResult")

        if recovery.state is not ExternalRecoveryState.RESUMED:
            return RecoveryContinuationResult(
                state=RecoveryContinuationState.NOT_READY,
                task_id=request.task_id,
                workflow_id=request.workflow_id,
                run_id=recovery.run_id,
                message="recovery has not resumed the original Task",
            )

        if not ExternalAgentRecoveryService.verify_continuity(
            request,
            recovery,
        ):
            return RecoveryContinuationResult(
                state=RecoveryContinuationState.BLOCKED,
                task_id=request.task_id,
                workflow_id=request.workflow_id,
                run_id=recovery.run_id,
                message="recovery continuity verification failed",
            )

        return RecoveryContinuationResult(
            state=RecoveryContinuationState.CONTINUED,
            task_id=request.task_id,
            workflow_id=request.workflow_id,
            run_id=recovery.run_id,
            message="original Workflow/Task/Run continuation is authorized",
        )


__all__ = [
    "ExternalAgentRecoveryContinuationService",
    "RecoveryContinuationResult",
    "RecoveryContinuationState",
]
