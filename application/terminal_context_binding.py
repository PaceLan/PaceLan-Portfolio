"""Binding between a terminal session and an execution context."""
from dataclasses import dataclass

from application.execution_context import ExecutionContext
from application.terminal_session_binding import TerminalSessionBinding


@dataclass(frozen=True)
class TerminalContextBinding:
    terminal: TerminalSessionBinding
    context: ExecutionContext

    def __post_init__(self) -> None:
        if not isinstance(self.terminal, TerminalSessionBinding):
            raise TypeError(
                "terminal must be a TerminalSessionBinding"
            )
        if not isinstance(self.context, ExecutionContext):
            raise TypeError("context must be an ExecutionContext")

        if self.context.terminal_id != self.terminal.terminal_id:
            raise ValueError(
                "terminal_id does not match execution context"
            )

        if self.context.terminal_session_id != self.terminal.session_id:
            raise ValueError(
                "terminal_session_id does not match execution context"
            )

        terminal_state = self.terminal.state.value
        if self.context.terminal_state != terminal_state:
            raise ValueError(
                "terminal_state does not match terminal session"
            )

    @property
    def terminal_id(self) -> str:
        return self.terminal.terminal_id

    @property
    def session_id(self) -> str:
        return self.terminal.session_id

    @property
    def terminal_state(self) -> str:
        return self.terminal.state.value

    @property
    def run_id(self) -> str:
        return self.context.run_id

    @property
    def task_id(self) -> str:
        return self.context.task_id


def bind_terminal_context(
    terminal: TerminalSessionBinding,
    context: ExecutionContext,
) -> TerminalContextBinding:
    return TerminalContextBinding(
        terminal=terminal,
        context=context,
    )
