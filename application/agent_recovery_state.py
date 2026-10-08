from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AgentRecoveryPhase(str, Enum):
    DETECTED = "DETECTED"
    READY = "READY"
    RECONNECTING = "RECONNECTING"
    RECONNECTED = "RECONNECTED"
    RESUMING = "RESUMING"
    RESUMED = "RESUMED"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    FAILED = "FAILED"
    COMPLETED = "COMPLETED"


@dataclass(frozen=True)
class AgentRecoveryState:
    recovery_id: str
    project_id: str
    task_id: str
    workflow_id: str | None
    run_id: str | None
    session_id: str | None
    phase: AgentRecoveryPhase
    task_status: str | None = None
    connection_state: str | None = None
    recoverable: bool = False
    retry_attempt: int = 0
    retry_limit: int | None = None
    reason: str = ""
    error: str | None = None
    updated_at: str | None = None
    sequence: int = 0

    def __post_init__(self) -> None:
        if not self.recovery_id.strip():
            raise ValueError("recovery_id must not be empty")
        if not self.project_id.strip():
            raise ValueError("project_id must not be empty")
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")
        if self.workflow_id is not None and not self.workflow_id.strip():
            raise ValueError("workflow_id must not be empty")
        if self.run_id is not None and not self.run_id.strip():
            raise ValueError("run_id must not be empty")
        if self.session_id is not None and not self.session_id.strip():
            raise ValueError("session_id must not be empty")
        if self.retry_attempt < 0:
            raise ValueError("retry_attempt must not be negative")
        if self.retry_limit is not None and self.retry_limit < 0:
            raise ValueError("retry_limit must not be negative")
        if self.sequence < 0:
            raise ValueError("sequence must not be negative")


__all__ = ["AgentRecoveryPhase", "AgentRecoveryState"]
