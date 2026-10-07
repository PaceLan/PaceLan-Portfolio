"""Binding between PacePilot TerminalSession and VS Code terminal."""

from __future__ import annotations

from dataclasses import dataclass, replace

from application.terminal_session import TerminalSession, TerminalSessionState
from application.vscode_control_channel import (
    TerminalControlResult,
    VSCodeControlChannel,
)


_REMOTE_STATES = {
    "CREATED": TerminalSessionState.CREATED,
    "RUNNING": TerminalSessionState.RUNNING,
    "CLOSED": TerminalSessionState.CLOSED,
    "FAILED": TerminalSessionState.FAILED,
    "DISCONNECTED": TerminalSessionState.DISCONNECTED,
}


@dataclass(frozen=True)
class TerminalSessionBinding:
    session: TerminalSession
    terminal_id: str

    def __post_init__(self) -> None:
        if not isinstance(self.terminal_id, str) or not self.terminal_id:
            raise ValueError("terminal_id must be a non-empty string")

    @property
    def session_id(self) -> str:
        return self.session.session_id

    @property
    def state(self) -> TerminalSessionState:
        return self.session.state

    @classmethod
    def from_result(
        cls,
        session: TerminalSession,
        result: TerminalControlResult,
    ) -> "TerminalSessionBinding":
        if result.session_id != session.session_id:
            raise ValueError("session_id does not match TerminalSession")

        if not result.terminal_id:
            raise ValueError("terminal_id is required")

        return cls(
            session=replace(
                session,
                state=_state_from_remote(result.state),
            ),
            terminal_id=result.terminal_id,
        )

    def apply_result(
        self,
        result: TerminalControlResult,
    ) -> "TerminalSessionBinding":
        if result.session_id != self.session_id:
            raise ValueError("session_id does not match binding")

        if result.terminal_id != self.terminal_id:
            raise ValueError("terminal_id does not match binding")

        return replace(
            self,
            session=replace(
                self.session,
                state=_state_from_remote(result.state),
            ),
        )

    def send(
        self,
        channel: VSCodeControlChannel,
        command: str,
    ) -> "TerminalSessionBinding":
        result = channel.send(
            terminal_id=self.terminal_id,
            command=command,
            session_id=self.session_id,
        )
        return self.apply_result(result)

    def status(
        self,
        channel: VSCodeControlChannel,
    ) -> "TerminalSessionBinding":
        result = channel.status(
            terminal_id=self.terminal_id,
            session_id=self.session_id,
        )
        return self.apply_result(result)

    def close(
        self,
        channel: VSCodeControlChannel,
    ) -> "TerminalSessionBinding":
        result = channel.close(
            terminal_id=self.terminal_id,
            session_id=self.session_id,
        )
        return self.apply_result(result)


def create_terminal_session_binding(
    channel: VSCodeControlChannel,
    session: TerminalSession,
    name: str = "PacePilot",
) -> TerminalSessionBinding:
    result = channel.create(
        cwd=session.cwd,
        name=name,
        session_id=session.session_id,
    )
    return TerminalSessionBinding.from_result(session, result)


def _state_from_remote(value: str) -> TerminalSessionState:
    try:
        return _REMOTE_STATES[value]
    except KeyError as exc:
        raise ValueError(
            f"unsupported terminal state: {value}"
        ) from exc


__all__ = [
    "TerminalSessionBinding",
    "create_terminal_session_binding",
]
