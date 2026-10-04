from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from application.external_agent_transport import (
    ExternalAgentTransportState,
    ExternalAgentTransportStatus,
)


@dataclass
class LocalHTTPExternalAgentTransport:
    """Real HTTP transport for a local external Agent endpoint."""

    endpoint: str
    provider: str = "LOCAL_HTTP"
    timeout: float = 5.0

    def __post_init__(self) -> None:
        self._status = ExternalAgentTransportStatus(
            state=ExternalAgentTransportState.DISCONNECTED,
            provider=self.provider,
        )

    def status(self) -> ExternalAgentTransportStatus:
        return self._status

    def connect(self) -> ExternalAgentTransportStatus:
        try:
            request = Request(
                self.endpoint,
                method="GET",
                headers={"Accept": "application/json"},
            )
            with urlopen(request, timeout=self.timeout) as response:
                if not 200 <= response.status < 300:
                    raise RuntimeError(
                        f"endpoint returned HTTP {response.status}"
                    )

            self._status = ExternalAgentTransportStatus(
                state=ExternalAgentTransportState.CONNECTED,
                provider=self.provider,
                message="local HTTP endpoint connected",
            )
        except (HTTPError, URLError, OSError, RuntimeError) as exc:
            self._status = ExternalAgentTransportStatus(
                state=ExternalAgentTransportState.UNAVAILABLE,
                provider=self.provider,
                message=f"local HTTP endpoint unavailable: {exc}",
            )

        return self._status

    def disconnect(self) -> ExternalAgentTransportStatus:
        self._status = ExternalAgentTransportStatus(
            state=ExternalAgentTransportState.DISCONNECTED,
            provider=self.provider,
            message="local HTTP transport disconnected",
        )
        return self._status

    def send(self, message: str) -> str:
        if not isinstance(message, str):
            raise TypeError("message must be a string")

        if self._status.state is not ExternalAgentTransportState.CONNECTED:
            raise RuntimeError("local HTTP transport is not connected")

        payload = json.dumps({"message": message}).encode("utf-8")
        request = Request(
            self.endpoint,
            data=payload,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )

        try:
            with urlopen(request, timeout=self.timeout) as response:
                body = response.read().decode("utf-8")
        except (HTTPError, URLError, OSError) as exc:
            self._status = ExternalAgentTransportStatus(
                state=ExternalAgentTransportState.DISCONNECTED,
                provider=self.provider,
                message=f"local HTTP connection lost: {exc}",
            )
            raise RuntimeError("local HTTP connection lost") from exc

        try:
            decoded = json.loads(body)
        except json.JSONDecodeError:
            return body

        if isinstance(decoded, dict) and isinstance(decoded.get("message"), str):
            return decoded["message"]

        if isinstance(decoded, str):
            return decoded

        return body


__all__ = ["LocalHTTPExternalAgentTransport"]
