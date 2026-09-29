"""Application-layer commands for product-facing execution."""

from dataclasses import dataclass

from .models import TaskModel


@dataclass(frozen=True)
class ExecuteTaskCommand:
    """Immutable application command for executing one task."""

    task: TaskModel

    def __post_init__(self) -> None:
        if not isinstance(self.task, TaskModel):
            raise TypeError("task must be a TaskModel")


class ExecuteTaskCommandHandler:
    """Thin application boundary from command to execution service."""

    def __init__(self, execution_service) -> None:
        run = getattr(execution_service, "run", None)
        if not callable(run):
            raise TypeError(
                "execution_service must provide a callable run method"
            )
        self.execution_service = execution_service

    def handle(self, command: ExecuteTaskCommand):
        if not isinstance(command, ExecuteTaskCommand):
            raise TypeError(
                "command must be an ExecuteTaskCommand"
            )
        return self.execution_service.run(command.task)


ExecuteTaskHandler = ExecuteTaskCommandHandler
