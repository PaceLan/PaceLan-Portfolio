"""VS Code terminal control channel."""

from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class TerminalControlResult:
    operation: str
    terminal_id: str | None
    session_id: str | None
    state: str
    output: str = ""


class VSCodeControlChannel:
    """Application-side channel for real VS Code terminal control."""

    def __init__(self, endpoint: str, timeout: float = 3.0) -> None:
        if not endpoint.strip():
            raise ValueError("endpoint must not be empty")
        if timeout <= 0:
            raise ValueError("timeout must be positive")

        self._endpoint = endpoint.rstrip("/")
        self._timeout = timeout

    def _request(
        self,
        operation: str,
        **payload: object,
    ) -> TerminalControlResult:
        body = json.dumps(
            {"operation": operation, **payload}
        ).encode("utf-8")

        request = Request(
            self._endpoint,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        with urlopen(request, timeout=self._timeout) as response:
            result = json.loads(
                response.read().decode("utf-8")
            )

        if result.get("error"):
            raise RuntimeError(result["error"])

        return TerminalControlResult(
            operation=operation,
            terminal_id=result.get("terminal_id"),
            session_id=result.get("session_id"),
            state=result.get("state", "UNKNOWN"),
            output=result.get("output", ""),
        )

    def create(
        self,
        cwd: str,
        name: str = "PacePilot",
        session_id: str | None = None,
    ) -> TerminalControlResult:
        return self._request(
            "create",
            cwd=cwd,
            name=name,
            session_id=session_id,
        )

    def send(
        self,
        terminal_id: str,
        command: str,
        session_id: str | None = None,
    ) -> TerminalControlResult:
        return self._request(
            "send",
            terminal_id=terminal_id,
            command=command,
            session_id=session_id,
        )

    def close(
        self,
        terminal_id: str,
        session_id: str | None = None,
    ) -> TerminalControlResult:
        return self._request(
            "close",
            terminal_id=terminal_id,
            session_id=session_id,
        )

    def status(
        self,
        terminal_id: str | None = None,
        session_id: str | None = None,
    ) -> TerminalControlResult:
        return self._request(
            "status",
            terminal_id=terminal_id,
            session_id=session_id,
        )


__all__ = [
    "TerminalControlResult",
    "VSCodeControlChannel",
]
