"""Fail-closed execution of explicitly declared VS Code terminal commands."""
from __future__ import annotations

from threading import RLock
from time import monotonic, sleep
from uuid import uuid4

from application.terminal_session import TerminalSession
from application.terminal_session_binding import (
    TerminalSessionBinding,
    create_terminal_session_binding,
)


class VSCodeTerminalCommandExecutor:
    def __init__(self, channel, cwd: str, *, timeout: float = 60.0,
                 poll_interval: float = 0.2) -> None:
        if not isinstance(cwd, str) or not cwd:
            raise ValueError("cwd must be a non-empty string")
        if timeout <= 0 or poll_interval <= 0:
            raise ValueError("timeout and poll_interval must be positive")
        self._channel = channel
        self._cwd = cwd
        self._timeout = timeout
        self._poll_interval = poll_interval
        self._binding: TerminalSessionBinding | None = None
        self._lock = RLock()

    def execute(self, command: str) -> str:
        with self._lock:
            return self._execute_locked(command)

    def _execute_locked(self, command: str) -> str:
        if not isinstance(command, str) or not command.strip():
            raise ValueError("terminal command must be a non-empty string")
        with self._lock:
            if self._binding is None:
                session = TerminalSession(
                    session_id=str(uuid4()),
                    shell="vscode-integrated",
                    cwd=self._cwd,
                )
                self._binding = create_terminal_session_binding(
                    self._channel, session
                )
            binding = self._binding.send(self._channel, command)
            command_id = binding.command_id
            if not command_id:
                raise RuntimeError("terminal dispatch returned no command_id")
            deadline = monotonic() + self._timeout
            while True:
                status = binding.command_status
                code = binding.exit_code
                if status == "SUCCEEDED":
                    if type(code) is not int or code != 0:
                        raise RuntimeError(
                            f"terminal reported SUCCEEDED without trusted exit code 0: {code!r}"
                        )
                    if binding.output_status == "CAPTURED":
                        self._binding = binding
                        return binding.output
                    if binding.output_status in {"UNAVAILABLE", "ERROR"}:
                        raise RuntimeError(
                            f"terminal output capture {binding.output_status.lower()}"
                        )
                    if binding.output_status != "PENDING":
                        raise RuntimeError(
                            f"terminal output capture status is untrusted: {binding.output_status!r}"
                        )
                if status in {"FAILED", "CANCELLED", "TERMINATED"}:
                    raise RuntimeError(
                        f"terminal command {status.lower()} (exit_code={code!r})"
                    )
                if status not in {"RUNNING", "DISPATCHED", "UNKNOWN", "SUCCEEDED"}:
                    raise RuntimeError(f"unsupported terminal command status: {status!r}")
                if monotonic() >= deadline:
                    raise TimeoutError(
                        f"terminal command status unresolved after {self._timeout}s"
                    )
                sleep(min(self._poll_interval, max(0.0, deadline - monotonic())))
                binding = binding.status(self._channel, command_id=command_id)
                self._binding = binding
