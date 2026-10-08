from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from enum import Enum

from application.chatgpt_interruption import (
    ChatGPTInterruption,
    ChatGPTInterruptionType,
)


class QuickCheckRecoveryState(str, Enum):
    EXIT_REQUIRED = "EXIT_REQUIRED"
    WAITING_FOR_RECOVERY = "WAITING_FOR_RECOVERY"


@dataclass(frozen=True)
class QuickCheckRecoveryResult:
    state: QuickCheckRecoveryState
    task_id: str
    workflow_id: str | None
    project_id: str | None
    detected_at: datetime
    waiting_until: datetime
    message: str

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")
        if self.detected_at.tzinfo is None:
            raise ValueError("detected_at must be timezone-aware")
        if self.waiting_until.tzinfo is None:
            raise ValueError("waiting_until must be timezone-aware")
        if self.waiting_until < self.detected_at:
            raise ValueError("waiting_until must not precede detected_at")


class ChatGPTQuickCheckRecoveryService:
    """Prepare the fixed exit-and-wait recovery path for Quick Check."""

    WAIT_SECONDS = 15 * 60

    def prepare(
        self,
        interruption: ChatGPTInterruption,
        *,
        task_id: str,
        detected_at: datetime | None = None,
        workflow_id: str | None = None,
        project_id: str | None = None,
    ) -> QuickCheckRecoveryResult:
        if not isinstance(interruption, ChatGPTInterruption):
            raise TypeError("interruption must be a ChatGPTInterruption")

        if interruption.interruption_type is not (
            ChatGPTInterruptionType.QUICK_CHECK_LIMIT
        ):
            raise ValueError(
                "interruption is not a Quick Check limitation"
            )

        if not task_id.strip():
            raise ValueError("task_id must not be empty")

        detected = detected_at or datetime.now(timezone.utc)
        if detected.tzinfo is None:
            raise ValueError("detected_at must be timezone-aware")

        waiting_until = detected + timedelta(seconds=self.WAIT_SECONDS)

        return QuickCheckRecoveryResult(
            state=QuickCheckRecoveryState.WAITING_FOR_RECOVERY,
            task_id=task_id,
            workflow_id=workflow_id,
            project_id=project_id,
            detected_at=detected,
            waiting_until=waiting_until,
            message=(
                interruption.message
                or "Quick Check limitation reached; exit ChatGPT "
                "and wait before recovery checks"
            ),
        )


__all__ = [
    "ChatGPTQuickCheckRecoveryService",
    "QuickCheckRecoveryResult",
    "QuickCheckRecoveryState",
]
