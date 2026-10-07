"""Terminal session state model for autonomous execution."""

from dataclasses import dataclass
from enum import Enum


class TerminalSessionState(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    CLOSED = "CLOSED"
    FAILED = "FAILED"
    DISCONNECTED = "DISCONNECTED"


@dataclass(frozen=True)
class TerminalSession:
    session_id: str
    shell: str
    cwd: str
    process_id: int | None = None
    state: TerminalSessionState = TerminalSessionState.CREATED

    def __post_init__(self) -> None:
        if not isinstance(self.session_id, str) or not self.session_id:
            raise ValueError("session_id must be a non-empty string")

        if not isinstance(self.shell, str) or not self.shell:
            raise ValueError("shell must be a non-empty string")

        if not isinstance(self.cwd, str) or not self.cwd:
            raise ValueError("cwd must be a non-empty string")

        if self.process_id is not None and (
            not isinstance(self.process_id, int) or self.process_id <= 0
        ):
            raise ValueError("process_id must be a positive integer or None")

        if not isinstance(self.state, TerminalSessionState):
            raise TypeError("state must be a TerminalSessionState")


__all__ = ["TerminalSession", "TerminalSessionState"]
