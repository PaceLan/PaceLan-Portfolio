"""Persistent execution context model for autonomous execution."""
from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class ExecutionContext:
    project_id: str
    task_id: str
    run_id: str
    step_id: str
    command_id: str | None = None
    workflow_id: str | None = None
    process_id: int | None = None
    process_state: str | None = None
    terminal_id: str | None = None
    terminal_session_id: str | None = None
    terminal_state: str | None = None
    execution_state: str = "UNKNOWN"
    recoverability: str = "UNKNOWN"
    checkpoint_sequence: int = 0
    checkpointed_at: datetime | None = None

    def __post_init__(self) -> None:
        for name in (
            "project_id",
            "task_id",
            "run_id",
            "step_id",
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must not be empty")

        for name in (
            "command_id",
            "workflow_id",
            "process_state",
            "terminal_id",
            "terminal_session_id",
            "terminal_state",
            "execution_state",
            "recoverability",
        ):
            value = getattr(self, name)
            if value is not None and (
                not isinstance(value, str) or not value.strip()
            ):
                raise ValueError(f"{name} must not be empty")

        if self.process_id is not None:
            if not isinstance(self.process_id, int) or self.process_id <= 0:
                raise ValueError("process_id must be positive")

        if not isinstance(self.checkpoint_sequence, int):
            raise TypeError("checkpoint_sequence must be an integer")
        if self.checkpoint_sequence < 0:
            raise ValueError("checkpoint_sequence must be non-negative")

        if self.workflow_id is not None and not self.workflow_id.strip():
            raise ValueError("workflow_id must not be empty")
