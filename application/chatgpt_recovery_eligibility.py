from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from application.chatgpt_interruption import (
    ChatGPTInterruptionType,
)
from application.chatgpt_timed_recovery_scheduler import RecoverySchedule


class RecoveryEligibility(str, Enum):
    IMMEDIATE_RECOVERY = "IMMEDIATE_RECOVERY"
    DELAYED_RECOVERY = "DELAYED_RECOVERY"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    NOT_RECOVERABLE = "NOT_RECOVERABLE"


@dataclass(frozen=True)
class RecoveryEligibilityResult:
    eligibility: RecoveryEligibility
    task_id: str
    workflow_id: str | None
    reason: str

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")
        if not self.reason.strip():
            raise ValueError("reason must not be empty")


class ChatGPTRecoveryEligibilityDetector:
    def detect(
        self,
        *,
        interruption_type: ChatGPTInterruptionType,
        task_id: str,
        workflow_id: str | None,
        recoverable: bool,
        now: datetime,
        schedule: RecoverySchedule | None = None,
        waiting_for_user: bool = False,
        waiting_external: bool = False,
    ) -> RecoveryEligibilityResult:
        if not isinstance(interruption_type, ChatGPTInterruptionType):
            raise TypeError("interruption_type must be a ChatGPTInterruptionType")
        if not task_id.strip():
            raise ValueError("task_id must not be empty")
        if now.tzinfo is None:
            raise ValueError("now must be timezone-aware")

        if waiting_for_user:
            return RecoveryEligibilityResult(
                eligibility=RecoveryEligibility.WAITING_FOR_USER,
                task_id=task_id,
                workflow_id=workflow_id,
                reason="user intervention is required before recovery",
            )

        if waiting_external:
            return RecoveryEligibilityResult(
                eligibility=RecoveryEligibility.WAITING_EXTERNAL,
                task_id=task_id,
                workflow_id=workflow_id,
                reason="external recovery condition is still pending",
            )

        if not recoverable:
            return RecoveryEligibilityResult(
                eligibility=RecoveryEligibility.NOT_RECOVERABLE,
                task_id=task_id,
                workflow_id=workflow_id,
                reason="recovery is not safely available",
            )

        if interruption_type is ChatGPTInterruptionType.SINGLE_CONVERSATION_LIMIT:
            return RecoveryEligibilityResult(
                eligibility=RecoveryEligibility.IMMEDIATE_RECOVERY,
                task_id=task_id,
                workflow_id=workflow_id,
                reason="single conversation limit can recover through a new conversation",
            )

        if interruption_type in (
            ChatGPTInterruptionType.GLOBAL_ANALYSIS_LIMIT,
            ChatGPTInterruptionType.QUICK_CHECK_LIMIT,
        ):
            if schedule is None:
                raise ValueError(
                    "schedule is required for timed recovery interruptions"
                )

            if now < schedule.next_check:
                return RecoveryEligibilityResult(
                    eligibility=RecoveryEligibility.DELAYED_RECOVERY,
                    task_id=task_id,
                    workflow_id=workflow_id,
                    reason="scheduled recovery check is not due yet",
                )

            return RecoveryEligibilityResult(
                eligibility=RecoveryEligibility.IMMEDIATE_RECOVERY,
                task_id=task_id,
                workflow_id=workflow_id,
                reason="scheduled recovery check is due",
            )

        return RecoveryEligibilityResult(
            eligibility=RecoveryEligibility.NOT_RECOVERABLE,
            task_id=task_id,
            workflow_id=workflow_id,
            reason="unknown interruption type cannot be safely recovered",
        )


__all__ = [
    "ChatGPTRecoveryEligibilityDetector",
    "RecoveryEligibility",
    "RecoveryEligibilityResult",
]
