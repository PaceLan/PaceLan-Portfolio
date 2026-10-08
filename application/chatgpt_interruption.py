from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ChatGPTInterruptionType(str, Enum):
    SINGLE_CONVERSATION_LIMIT = "SINGLE_CONVERSATION_LIMIT"
    GLOBAL_ANALYSIS_LIMIT = "GLOBAL_ANALYSIS_LIMIT"
    QUICK_CHECK_LIMIT = "QUICK_CHECK_LIMIT"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class ChatGPTInterruption:
    interruption_type: ChatGPTInterruptionType
    message: str = ""

    def __post_init__(self) -> None:
        if not isinstance(
            self.interruption_type,
            ChatGPTInterruptionType,
        ):
            raise TypeError(
                "interruption_type must be a ChatGPTInterruptionType"
            )


__all__ = [
    "ChatGPTInterruption",
    "ChatGPTInterruptionType",
]
