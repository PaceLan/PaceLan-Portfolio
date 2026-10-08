from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from application.chatgpt_interruption import (
    ChatGPTInterruption,
    ChatGPTInterruptionType,
)


class SingleConversationRecoveryState(str, Enum):
    NEW_CONVERSATION_REQUIRED = "NEW_CONVERSATION_REQUIRED"
    READY_TO_RESUME = "READY_TO_RESUME"


@dataclass(frozen=True)
class SingleConversationRecoveryResult:
    state: SingleConversationRecoveryState
    task_id: str
    workflow_id: str | None
    project_id: str | None
    message: str

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")


class ChatGPTSingleConversationRecoveryService:
    """Preserve the original Task across a single-conversation limit."""

    def prepare(
        self,
        interruption: ChatGPTInterruption,
        *,
        task_id: str,
        workflow_id: str | None = None,
        project_id: str | None = None,
    ) -> SingleConversationRecoveryResult:
        if not isinstance(interruption, ChatGPTInterruption):
            raise TypeError("interruption must be a ChatGPTInterruption")

        if interruption.interruption_type is not (
            ChatGPTInterruptionType.SINGLE_CONVERSATION_LIMIT
        ):
            raise ValueError(
                "interruption is not a single-conversation limit"
            )

        if not task_id.strip():
            raise ValueError("task_id must not be empty")

        return SingleConversationRecoveryResult(
            state=SingleConversationRecoveryState.NEW_CONVERSATION_REQUIRED,
            task_id=task_id,
            workflow_id=workflow_id,
            project_id=project_id,
            message=(
                interruption.message
                or "single conversation limit reached; "
                "a new conversation is required"
            ),
        )

    def mark_ready(
        self,
        result: SingleConversationRecoveryResult,
    ) -> SingleConversationRecoveryResult:
        if not isinstance(result, SingleConversationRecoveryResult):
            raise TypeError(
                "result must be a SingleConversationRecoveryResult"
            )

        return SingleConversationRecoveryResult(
            state=SingleConversationRecoveryState.READY_TO_RESUME,
            task_id=result.task_id,
            workflow_id=result.workflow_id,
            project_id=result.project_id,
            message="new conversation is ready to resume the original Task",
        )


__all__ = [
    "ChatGPTSingleConversationRecoveryService",
    "SingleConversationRecoveryResult",
    "SingleConversationRecoveryState",
]
