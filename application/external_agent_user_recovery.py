from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from application.external_agent_recovery import (
    ExternalRecoveryResult,
    ExternalRecoveryState,
)


class ExternalUserRecoveryState(str, Enum):
    WAITING_FOR_USER = "WAITING_FOR_USER"


@dataclass(frozen=True)
class ExternalUserRecoveryResult:
    state: ExternalUserRecoveryState
    project_id: str | None
    task_id: str
    workflow_id: str | None
    run_id: str | None
    reason: str
    action_required: str
    recoverable: bool = True

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")
        if not self.reason.strip():
            raise ValueError("reason must not be empty")
        if not self.action_required.strip():
            raise ValueError("action_required must not be empty")
        if not self.recoverable:
            raise ValueError("user recovery requires a recoverable task")


class ExternalAgentUserRecoveryService:
    """Expose unresolved recoverable Agent recovery as explicit user work."""

    _USER_ACTION_STATES = {
        ExternalRecoveryState.SESSION_NOT_AVAILABLE,
        ExternalRecoveryState.PERSISTED_ONLY,
    }

    def present(
        self,
        result: ExternalRecoveryResult,
        *,
        action_required: str,
    ) -> ExternalUserRecoveryResult:
        if not isinstance(result, ExternalRecoveryResult):
            raise TypeError("result must be an ExternalRecoveryResult")
        if not action_required.strip():
            raise ValueError("action_required must not be empty")
        if not result.recoverable:
            raise ValueError(
                "non-recoverable Agent state cannot enter user recovery"
            )
        if result.state not in self._USER_ACTION_STATES:
            raise ValueError(
                "Agent recovery result does not require user intervention"
            )

        return ExternalUserRecoveryResult(
            state=ExternalUserRecoveryState.WAITING_FOR_USER,
            project_id=result.project_id,
            task_id=result.task_id,
            workflow_id=result.workflow_id,
            run_id=result.run_id,
            reason=result.message or "silent Agent recovery could not continue",
            action_required=action_required,
        )


__all__ = [
    "ExternalAgentUserRecoveryService",
    "ExternalUserRecoveryResult",
    "ExternalUserRecoveryState",
]
