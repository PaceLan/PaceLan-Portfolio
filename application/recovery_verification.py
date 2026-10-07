from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Callable

from application.recovery_execution import RecoveryExecution, RecoveryExecutionResult


class RecoveryVerification(str, Enum):
    VERIFIED = "VERIFIED"
    NOT_VERIFIED = "NOT_VERIFIED"
    WAITING = "WAITING"


@dataclass(frozen=True)
class RecoveryVerificationResult:
    status: RecoveryVerification
    verified: bool
    actual_state: str | None
    expected_state: str
    message: str = ""


class RecoveryVerificationService:
    """Verify recovery against the real post-recovery runtime state."""

    def __init__(
        self,
        state_reader: Callable[[], object] | None = None,
    ) -> None:
        self._state_reader = state_reader

    def verify(
        self,
        result: RecoveryExecutionResult,
        *,
        expected_state: str,
    ) -> RecoveryVerificationResult:
        if not isinstance(result, RecoveryExecutionResult):
            raise TypeError("result must be a RecoveryExecutionResult")
        if not isinstance(expected_state, str) or not expected_state.strip():
            raise ValueError("expected_state must be a non-empty string")

        expected = expected_state.strip()

        if result.outcome in {
            RecoveryExecution.WAITING_EXTERNAL,
            RecoveryExecution.WAITING_FOR_USER,
        }:
            return RecoveryVerificationResult(
                status=RecoveryVerification.WAITING,
                verified=False,
                actual_state=None,
                expected_state=expected,
                message="recovery is waiting and cannot be verified yet",
            )

        if (
            result.outcome is not RecoveryExecution.IMMEDIATE_RECOVERY
            or not result.executed
            or not result.succeeded
        ):
            return RecoveryVerificationResult(
                status=RecoveryVerification.NOT_VERIFIED,
                verified=False,
                actual_state=None,
                expected_state=expected,
                message=result.message or "recovery execution did not succeed",
            )

        if self._state_reader is None:
            return RecoveryVerificationResult(
                status=RecoveryVerification.NOT_VERIFIED,
                verified=False,
                actual_state=None,
                expected_state=expected,
                message="no real runtime state reader is configured",
            )

        try:
            actual_value = self._state_reader()
        except Exception as exc:
            return RecoveryVerificationResult(
                status=RecoveryVerification.NOT_VERIFIED,
                verified=False,
                actual_state=None,
                expected_state=expected,
                message=f"runtime state verification failed: {exc}",
            )

        actual = str(actual_value).strip()

        if actual != expected:
            return RecoveryVerificationResult(
                status=RecoveryVerification.NOT_VERIFIED,
                verified=False,
                actual_state=actual,
                expected_state=expected,
                message=f"expected {expected}, observed {actual}",
            )

        return RecoveryVerificationResult(
            status=RecoveryVerification.VERIFIED,
            verified=True,
            actual_state=actual,
            expected_state=expected,
            message="recovery state verified",
        )


__all__ = [
    "RecoveryVerification",
    "RecoveryVerificationResult",
    "RecoveryVerificationService",
]
