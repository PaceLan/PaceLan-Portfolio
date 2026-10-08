from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from application.external_agent import ExternalAgentRequest


class ExternalAgentSessionState(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    ATTACHED = "ATTACHED"


@dataclass(frozen=True)
class ExternalAgentSessionStatus:
    session_id: str
    state: ExternalAgentSessionState
    message: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.session_id, str) or not self.session_id.strip():
            raise ValueError("session_id must not be empty")


class ExternalAgentSessionCapability(Protocol):
    """Optional provider capability for reusing an existing external session."""

    def inspect_session(
        self,
        session_id: str,
        request: ExternalAgentRequest,
    ) -> ExternalAgentSessionStatus:
        ...

    def attach_session(
        self,
        session_id: str,
        request: ExternalAgentRequest,
    ) -> ExternalAgentSessionStatus:
        ...


__all__ = [
    "ExternalAgentSessionCapability",
    "ExternalAgentSessionState",
    "ExternalAgentSessionStatus",
]
