from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExternalAgentRetryDecision(str, Enum):
    RETRY = "RETRY"
    STOP = "STOP"


@dataclass(frozen=True)
class ExternalAgentRetryResult:
    decision: ExternalAgentRetryDecision
    attempt: int
    max_attempts: int
    delay_seconds: float = 0.0
    message: str = ""


class ExternalAgentRetryPolicy:
    """Bounded retry policy for external Agent recovery."""

    def __init__(
        self,
        *,
        max_attempts: int = 3,
        retry_delay_seconds: float = 1.0,
    ) -> None:
        if not isinstance(max_attempts, int) or isinstance(max_attempts, bool):
            raise TypeError("max_attempts must be an integer")
        if max_attempts <= 0:
            raise ValueError("max_attempts must be greater than zero")
        if (
            not isinstance(retry_delay_seconds, (int, float))
            or isinstance(retry_delay_seconds, bool)
        ):
            raise TypeError("retry_delay_seconds must be a number")
        if retry_delay_seconds < 0:
            raise ValueError("retry_delay_seconds must not be negative")
        self._max_attempts = max_attempts
        self._retry_delay_seconds = float(retry_delay_seconds)

    @property
    def max_attempts(self) -> int:
        return self._max_attempts

    @property
    def retry_delay_seconds(self) -> float:
        return self._retry_delay_seconds

    def decide(self, *, attempt: int) -> ExternalAgentRetryResult:
        if not isinstance(attempt, int) or isinstance(attempt, bool):
            raise TypeError("attempt must be an integer")
        if attempt < 0:
            raise ValueError("attempt must not be negative")

        if attempt >= self._max_attempts:
            return ExternalAgentRetryResult(
                decision=ExternalAgentRetryDecision.STOP,
                attempt=attempt,
                max_attempts=self._max_attempts,
                delay_seconds=0.0,
                message="external Agent recovery retry limit reached",
            )

        return ExternalAgentRetryResult(
            decision=ExternalAgentRetryDecision.RETRY,
            attempt=attempt,
            max_attempts=self._max_attempts,
            delay_seconds=self._retry_delay_seconds,
            message="external Agent recovery retry is permitted",
        )


__all__ = [
    "ExternalAgentRetryDecision",
    "ExternalAgentRetryPolicy",
    "ExternalAgentRetryResult",
]
