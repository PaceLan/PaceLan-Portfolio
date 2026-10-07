"""Process lifecycle state model for autonomous execution."""

from dataclasses import dataclass
from enum import Enum
from typing import FrozenSet


class ProcessLifecycleState(str, Enum):
    STARTING = "STARTING"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    EXITED = "EXITED"
    FAILED = "FAILED"
    CRASHED = "CRASHED"
    HUNG = "HUNG"


@dataclass(frozen=True)
class ProcessSnapshot:
    process_id: int | None
    state: ProcessLifecycleState
    exit_code: int | None = None
    started_at: object | None = None
    finished_at: object | None = None

    def __post_init__(self) -> None:
        if self.process_id is not None and (
            not isinstance(self.process_id, int) or self.process_id <= 0
        ):
            raise ValueError("process_id must be a positive integer or None")

        if not isinstance(self.state, ProcessLifecycleState):
            raise TypeError("state must be a ProcessLifecycleState")

        if self.exit_code is not None and not isinstance(self.exit_code, int):
            raise TypeError("exit_code must be an integer or None")


TERMINAL_PROCESS_STATES: FrozenSet[ProcessLifecycleState] = frozenset(
    {
        ProcessLifecycleState.EXITED,
        ProcessLifecycleState.FAILED,
        ProcessLifecycleState.CRASHED,
    }
)


__all__ = [
    "ProcessLifecycleState",
    "ProcessSnapshot",
    "TERMINAL_PROCESS_STATES",
]
