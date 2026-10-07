from __future__ import annotations

from application.task_context import TaskContext
from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ExternalConnectionState(str, Enum):
    DISCONNECTED = "disconnected"
    CONNECTED = "connected"
    WAITING_EXTERNAL = "waiting_external"
    RECOVERABLE = "recoverable"
    FAILED = "failed"


class ExternalConnectionReason(str, Enum):
    NONE = "none"
    SAFETY_CHECK = "safety_check"
    QUOTA_LIMIT = "quota_limit"
    CONNECTION_LOST = "connection_lost"


@dataclass(frozen=True)
class ExternalAgentStatus:
    state: ExternalConnectionState
    reason: ExternalConnectionReason = ExternalConnectionReason.NONE
    recoverable: bool = False
    message: str = ""

    def __post_init__(self) -> None:
        if self.state is ExternalConnectionState.WAITING_EXTERNAL:
            if self.reason is ExternalConnectionReason.NONE:
                raise ValueError(
                    "WAITING_EXTERNAL requires an external reason"
                )

        if self.state is ExternalConnectionState.RECOVERABLE:
            if not self.recoverable:
                raise ValueError(
                    "RECOVERABLE state requires recoverable=True"
                )

        if self.state in {
            ExternalConnectionState.CONNECTED,
            ExternalConnectionState.DISCONNECTED,
            ExternalConnectionState.FAILED,
        } and self.recoverable:
            raise ValueError(
                "recoverable=True is only valid for recoverable states"
            )


@dataclass(frozen=True)
class ExternalAgentRequest:
    task_id: str
    payload: str
    workflow_id: str | None = None

    def to_task_context(self, project_id: str) -> TaskContext:
        return TaskContext(
            project_id=project_id,
            task_id=self.task_id,
            workflow_id=self.workflow_id,
        )


@dataclass(frozen=True)
class ExternalAgentResponse:
    task_id: str
    payload: str
    workflow_id: str | None = None


class ExternalAgentAdapter(Protocol):
    def status(self) -> ExternalAgentStatus:
        ...

    def send(
        self,
        request: ExternalAgentRequest,
    ) -> ExternalAgentResponse:
        ...

    def resume(
        self,
        request: ExternalAgentRequest,
    ) -> ExternalAgentResponse:
        ...
