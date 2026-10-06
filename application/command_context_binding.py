"""Binding between a planned command and its persistent execution context."""
from dataclasses import dataclass

from application.command_planning import Command
from application.execution_context import ExecutionContext


@dataclass(frozen=True)
class CommandContextBinding:
    command: Command
    context: ExecutionContext

    def __post_init__(self) -> None:
        if not isinstance(self.command, Command):
            raise TypeError("command must be a Command")
        if not isinstance(self.context, ExecutionContext):
            raise TypeError("context must be an ExecutionContext")

        pairs = (
            ("project_id", self.command.project_id, self.context.project_id),
            ("task_id", self.command.task_id, self.context.task_id),
            ("step_id", self.command.step_id, self.context.step_id),
        )
        for name, command_value, context_value in pairs:
            if command_value != context_value:
                raise ValueError(
                    f"{name} does not match execution context"
                )

    @property
    def command_id(self) -> str | None:
        return self.context.command_id

    @property
    def project_id(self) -> str:
        return self.context.project_id

    @property
    def task_id(self) -> str:
        return self.context.task_id

    @property
    def step_id(self) -> str:
        return self.context.step_id

    @property
    def run_id(self) -> str:
        return self.context.run_id


def bind_command_context(
    command: Command,
    context: ExecutionContext,
) -> CommandContextBinding:
    return CommandContextBinding(command=command, context=context)
