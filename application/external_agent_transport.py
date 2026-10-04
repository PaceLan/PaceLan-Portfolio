"""Transport boundary for real external Agent connections."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class ExternalAgentTransportState(str, Enum):
    AVAILABLE = "AVAILABLE"
    UNAVAILABLE = "UNAVAILABLE"
    CONNECTING = "CONNECTING"
    CONNECTED = "CONNECTED"
    DISCONNECTED = "DISCONNECTED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class ExternalAgentTransportStatus:
    state: ExternalAgentTransportState
    provider: str
    message: str = ""

    @property
    def available(self) -> bool:
        return self.state is ExternalAgentTransportState.CONNECTED


class ExternalAgentTransport(Protocol):
    """Provider-neutral transport contract for a real external Agent."""

    def connect(self) -> ExternalAgentTransportStatus: ...

    def disconnect(self) -> ExternalAgentTransportStatus: ...

    def status(self) -> ExternalAgentTransportStatus: ...

    def send(self, message: str) -> str: ...


class ExternalAgentTransportUnavailableError(RuntimeError):
    """Raised when no real external transport is configured."""


@dataclass
class UnavailableExternalAgentTransport:
    """Explicit no-transport implementation; never pretends to be connected."""

    provider: str = "UNCONFIGURED"

    def status(self) -> ExternalAgentTransportStatus:
        return ExternalAgentTransportStatus(
            state=ExternalAgentTransportState.UNAVAILABLE,
            provider=self.provider,
            message="no real external Agent transport is configured",
        )

    def connect(self) -> ExternalAgentTransportStatus:
        return self.status()

    def disconnect(self) -> ExternalAgentTransportStatus:
        return ExternalAgentTransportStatus(
            state=ExternalAgentTransportState.DISCONNECTED,
            provider=self.provider,
            message="external Agent transport was not connected",
        )

    def send(self, message: str) -> str:
        if not isinstance(message, str):
            raise TypeError("message must be a string")
        raise ExternalAgentTransportUnavailableError(
            "no real external Agent transport is configured"
        )


__all__ = [
    "ExternalAgentTransport",
    "ExternalAgentTransportState",
    "ExternalAgentTransportStatus",
    "ExternalAgentTransportUnavailableError",
    "UnavailableExternalAgentTransport",
]
