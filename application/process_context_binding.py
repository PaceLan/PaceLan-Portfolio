"""Binding between a process snapshot and an execution context."""
from dataclasses import dataclass

from application.execution_context import ExecutionContext
from application.process_lifecycle import ProcessSnapshot


@dataclass(frozen=True)
class ProcessContextBinding:
    snapshot: ProcessSnapshot
    context: ExecutionContext

    def __post_init__(self) -> None:
        if not isinstance(self.snapshot, ProcessSnapshot):
            raise TypeError("snapshot must be a ProcessSnapshot")
        if not isinstance(self.context, ExecutionContext):
            raise TypeError("context must be an ExecutionContext")

        if self.context.process_id != self.snapshot.process_id:
            raise ValueError("process_id does not match execution context")

        snapshot_state = self.snapshot.state.value
        if self.context.process_state != snapshot_state:
            raise ValueError("process_state does not match process snapshot")

    @property
    def process_id(self) -> int:
        return self.snapshot.process_id

    @property
    def process_state(self) -> str:
        return self.snapshot.state.value

    @property
    def run_id(self) -> str:
        return self.context.run_id

    @property
    def task_id(self) -> str:
        return self.context.task_id


def bind_process_context(
    snapshot: ProcessSnapshot,
    context: ExecutionContext,
) -> ProcessContextBinding:
    return ProcessContextBinding(snapshot=snapshot, context=context)
