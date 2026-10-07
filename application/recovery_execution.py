from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from application.recovery_decision import RecoveryDecision


class RecoveryExecution(str, Enum):
    IMMEDIATE_RECOVERY = "IMMEDIATE_RECOVERY"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    STOP = "STOP"
    FAILED = "FAILED"


@dataclass(frozen=True)
class RecoveryExecutionResult:
    outcome: RecoveryExecution
    executed: bool
    succeeded: bool
    message: str = ""


class RecoveryExecutionService:
    """Execute only an approved immediate recovery action."""

    def __init__(
        self,
        immediate_recovery: Callable[[], object] | None = None,
    ) -> None:
        self._immediate_recovery = immediate_recovery

    def execute(self, decision: RecoveryDecision) -> RecoveryExecutionResult:
        if not isinstance(decision, RecoveryDecision):
            raise TypeError("decision must be a RecoveryDecision")

        if decision is RecoveryDecision.WAITING_EXTERNAL:
            return RecoveryExecutionResult(
                outcome=RecoveryExecution.WAITING_EXTERNAL,
                executed=False,
                succeeded=False,
                message="waiting for external dependency",
            )

        if decision is RecoveryDecision.WAITING_FOR_USER:
            return RecoveryExecutionResult(
                outcome=RecoveryExecution.WAITING_FOR_USER,
                executed=False,
                succeeded=False,
                message="waiting for user intervention",
            )

        if decision is RecoveryDecision.STOP:
            return RecoveryExecutionResult(
                outcome=RecoveryExecution.STOP,
                executed=False,
                succeeded=False,
                message="recovery execution stopped",
            )

        if self._immediate_recovery is None:
            return RecoveryExecutionResult(
                outcome=RecoveryExecution.FAILED,
                executed=False,
                succeeded=False,
                message="no immediate recovery action is configured",
            )

        try:
            self._immediate_recovery()
        except Exception as exc:
            return RecoveryExecutionResult(
                outcome=RecoveryExecution.FAILED,
                executed=True,
                succeeded=False,
                message=str(exc),
            )

        return RecoveryExecutionResult(
            outcome=RecoveryExecution.IMMEDIATE_RECOVERY,
            executed=True,
            succeeded=True,
            message="recovery action completed",
        )


__all__ = [
    "RecoveryExecution",
    "RecoveryExecutionResult",
    "RecoveryExecutionService",
]
