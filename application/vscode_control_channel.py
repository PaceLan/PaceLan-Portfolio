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
    output_status: str = "UNKNOWN"
    command_id: str | None = None
    command_status: str = "UNKNOWN"
    exit_code: int | None = None


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
            output_status=result.get("output_status", "UNKNOWN"),
            command_id=result.get("command_id"),
            command_status=result.get("command_status", "UNKNOWN"),
            exit_code=result.get("exit_code"),
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
        command_id: str | None = None,
    ) -> TerminalControlResult:
        payload = {
            "terminal_id": terminal_id,
            "session_id": session_id,
        }
        if command_id is not None:
            payload["command_id"] = command_id
        return self._request("status", **payload)


__all__ = [
    "TerminalControlResult",
    "VSCodeControlChannel",
]
