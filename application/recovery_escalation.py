from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from application.recovery_verification import (
    RecoveryVerification,
    RecoveryVerificationResult,
)


class RecoveryEscalation(str, Enum):
    COMPLETED = "COMPLETED"
    WAITING = "WAITING"
    ESCALATE = "ESCALATE"
    STOP = "STOP"


@dataclass(frozen=True)
class RecoveryEscalationResult:
    outcome: RecoveryEscalation
    attempt: int
    max_attempts: int
    message: str = ""


class RecoveryEscalationService:
    """Decide escalation after recovery verification without executing actions."""

    def __init__(self, *, max_attempts: int = 1) -> None:
        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool):
            raise TypeError("max_attempts must be an integer")
        if max_attempts <= 0:
            raise ValueError("max_attempts must be greater than zero")
        self._max_attempts = max_attempts

    def decide(
        self,
        verification: RecoveryVerificationResult,
        *,
        attempt: int,
    ) -> RecoveryEscalationResult:
        if not isinstance(verification, RecoveryVerificationResult):
            raise TypeError(
                "verification must be a RecoveryVerificationResult"
            )
        if not isinstance(attempt, int) or isinstance(attempt, bool):
            raise TypeError("attempt must be an integer")
        if attempt < 0:
            raise ValueError("attempt must not be negative")

        if verification.status is RecoveryVerification.VERIFIED:
            return RecoveryEscalationResult(
                outcome=RecoveryEscalation.COMPLETED,
                attempt=attempt,
                max_attempts=self._max_attempts,
                message="recovery verification completed",
            )

        if verification.status is RecoveryVerification.WAITING:
            return RecoveryEscalationResult(
                outcome=RecoveryEscalation.WAITING,
                attempt=attempt,
                max_attempts=self._max_attempts,
                message="recovery verification is waiting",
            )

        if attempt >= self._max_attempts:
            return RecoveryEscalationResult(
                outcome=RecoveryEscalation.STOP,
                attempt=attempt,
                max_attempts=self._max_attempts,
                message="recovery escalation limit reached",
            )

        return RecoveryEscalationResult(
            outcome=RecoveryEscalation.ESCALATE,
            attempt=attempt,
            max_attempts=self._max_attempts,
            message="recovery verification failed; escalation required",
        )


__all__ = [
    "RecoveryEscalation",
    "RecoveryEscalationResult",
    "RecoveryEscalationService",
]
