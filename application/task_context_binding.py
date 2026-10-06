"""Binding between the task context and an execution context."""
from dataclasses import dataclass

from application.execution_context import ExecutionContext
from application.task_context import TaskContext


@dataclass(frozen=True)
class TaskContextBinding:
    task: TaskContext
    context: ExecutionContext

    def __post_init__(self) -> None:
        if not isinstance(self.task, TaskContext):
            raise TypeError("task must be a TaskContext")
        if not isinstance(self.context, ExecutionContext):
            raise TypeError("context must be an ExecutionContext")

        if self.task.project_id != self.context.project_id:
            raise ValueError(
                "project_id does not match execution context"
            )

        if self.task.task_id != self.context.task_id:
            raise ValueError(
                "task_id does not match execution context"
            )

        if self.task.workflow_id != self.context.workflow_id:
            raise ValueError(
                "workflow_id does not match execution context"
            )

    @property
    def project_id(self) -> str:
        return self.task.project_id

    @property
    def task_id(self) -> str:
        return self.task.task_id

    @property
    def workflow_id(self) -> str | None:
        return self.task.workflow_id

    @property
    def run_id(self) -> str:
        return self.context.run_id


def bind_task_context(
    task: TaskContext,
    context: ExecutionContext,
) -> TaskContextBinding:
    return TaskContextBinding(task=task, context=context)
