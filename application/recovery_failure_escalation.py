from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RecoveryEscalationLevel(str, Enum):
    LEVEL_1 = "LEVEL_1"
    LEVEL_2 = "LEVEL_2"
    LEVEL_3 = "LEVEL_3"


class RecoveryEscalationDecision(str, Enum):
    CONTINUE = "CONTINUE"
    ESCALATE = "ESCALATE"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    WAITING_FOR_USER = "WAITING_FOR_USER"


@dataclass(frozen=True)
class RecoveryEscalationResult:
    decision: RecoveryEscalationDecision
    current_level: RecoveryEscalationLevel
    next_level: RecoveryEscalationLevel | None
    task_id: str
    workflow_id: str | None
    run_id: str | None
    reason: str
    retry_exhausted: bool

    def __post_init__(self) -> None:
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")
        if not self.reason.strip():
            raise ValueError("reason must not be empty")


class RecoveryFailureEscalationService:
    """Escalate failed recovery through bounded recovery levels."""

    @staticmethod
    def _next_level(
        level: RecoveryEscalationLevel,
    ) -> RecoveryEscalationLevel | None:
        if level is RecoveryEscalationLevel.LEVEL_1:
            return RecoveryEscalationLevel.LEVEL_2
        if level is RecoveryEscalationLevel.LEVEL_2:
            return RecoveryEscalationLevel.LEVEL_3
        return None

    def decide(
        self,
        *,
        level: RecoveryEscalationLevel,
        task_id: str,
        workflow_id: str | None,
        run_id: str | None,
        recoverable: bool,
        retry_exhausted: bool,
        reason: str,
        waiting_external: bool = False,
        waiting_for_user: bool = False,
    ) -> RecoveryEscalationResult:
        if not isinstance(level, RecoveryEscalationLevel):
            raise TypeError(
                "level must be a RecoveryEscalationLevel"
            )
        if not task_id.strip():
            raise ValueError("task_id must not be empty")
        if not reason.strip():
            raise ValueError("reason must not be empty")

        if waiting_for_user:
            return RecoveryEscalationResult(
                decision=RecoveryEscalationDecision.WAITING_FOR_USER,
                current_level=level,
                next_level=None,
                task_id=task_id,
                workflow_id=workflow_id,
                run_id=run_id,
                reason=reason,
                retry_exhausted=retry_exhausted,
            )

        if waiting_external:
            return RecoveryEscalationResult(
                decision=RecoveryEscalationDecision.WAITING_EXTERNAL,
                current_level=level,
                next_level=None,
                task_id=task_id,
                workflow_id=workflow_id,
                run_id=run_id,
                reason=reason,
                retry_exhausted=retry_exhausted,
            )

        if not recoverable:
            return RecoveryEscalationResult(
                decision=RecoveryEscalationDecision.WAITING_FOR_USER,
                current_level=level,
                next_level=RecoveryEscalationLevel.LEVEL_3,
                task_id=task_id,
                workflow_id=workflow_id,
                run_id=run_id,
                reason=reason,
                retry_exhausted=retry_exhausted,
            )

        if level is RecoveryEscalationLevel.LEVEL_3:
            return RecoveryEscalationResult(
                decision=RecoveryEscalationDecision.WAITING_FOR_USER,
                current_level=level,
                next_level=None,
                task_id=task_id,
                workflow_id=workflow_id,
                run_id=run_id,
                reason=reason,
                retry_exhausted=retry_exhausted,
            )

        if retry_exhausted:
            next_level = self._next_level(level)
            return RecoveryEscalationResult(
                decision=RecoveryEscalationDecision.ESCALATE,
                current_level=level,
                next_level=next_level,
                task_id=task_id,
                workflow_id=workflow_id,
                run_id=run_id,
                reason=reason,
                retry_exhausted=True,
            )

        return RecoveryEscalationResult(
            decision=RecoveryEscalationDecision.CONTINUE,
            current_level=level,
            next_level=None,
            task_id=task_id,
            workflow_id=workflow_id,
            run_id=run_id,
            reason=reason,
            retry_exhausted=False,
        )


__all__ = [
    "RecoveryEscalationDecision",
    "RecoveryEscalationLevel",
    "RecoveryEscalationResult",
    "RecoveryFailureEscalationService",
]
