from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ExternalAPIState(str, Enum):
    CONNECTED = "Connected"
    DISCONNECTED = "Disconnected"
    RATE_LIMITED = "Rate Limited"
    QUOTA = "Quota"
    ERROR = "Error"
    UNAVAILABLE = "Unavailable"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ExternalAPIStateResult:
    state: ExternalAPIState
    message: str = ""


class ExternalAPIStateDetector:
    """Map explicit formal API state to a verified or UNKNOWN state."""

    _STATES = {
        "Connected": ExternalAPIState.CONNECTED,
        "Disconnected": ExternalAPIState.DISCONNECTED,
        "Rate Limited": ExternalAPIState.RATE_LIMITED,
        "Quota": ExternalAPIState.QUOTA,
        "Error": ExternalAPIState.ERROR,
        "Unavailable": ExternalAPIState.UNAVAILABLE,
    }

    def detect(
        self,
        formal_state: str | None,
        *,
        message: str = "",
    ) -> ExternalAPIStateResult:
        if formal_state is None:
            return ExternalAPIStateResult(
                state=ExternalAPIState.UNKNOWN,
                message=message or "formal API state is unavailable",
            )

        if not isinstance(formal_state, str):
            raise TypeError("formal_state must be a string or None")

        if not formal_state.strip():
            return ExternalAPIStateResult(
                state=ExternalAPIState.UNKNOWN,
                message=message or "formal API state is empty",
            )

        state = self._STATES.get(formal_state)
        if state is None:
            return ExternalAPIStateResult(
                state=ExternalAPIState.UNKNOWN,
                message=message or "formal API state cannot be verified",
            )

        return ExternalAPIStateResult(
            state=state,
            message=message,
        )


__all__ = [
    "ExternalAPIState",
    "ExternalAPIStateDetector",
    "ExternalAPIStateResult",
]
