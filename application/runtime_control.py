"""Application-layer runtime controls for active Agent execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class RuntimeControlState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    TERMINATED = "TERMINATED"


class RuntimeControlTarget(Protocol):
    def pause_runtime(self) -> None: ...
    def resume_runtime(self) -> None: ...
    def terminate_runtime(self) -> None: ...
    def runtime_state(self) -> str: ...


@dataclass(frozen=True)
class RuntimeControlResult:
    action: str
    state: RuntimeControlState
    accepted: bool
    message: str = ""


class ApplicationRuntimeControlService:
    """Application boundary for active Agent runtime control."""

    def __init__(self, target: RuntimeControlTarget) -> None:
        self._target = target

    def _state(self) -> RuntimeControlState:
        return RuntimeControlState(self._target.runtime_state())

    def pause(self) -> RuntimeControlResult:
        self._target.pause_runtime()
        return RuntimeControlResult(
            action="pause",
            state=self._state(),
            accepted=True,
        )

    def resume(self) -> RuntimeControlResult:
        self._target.resume_runtime()
        return RuntimeControlResult(
            action="resume",
            state=self._state(),
            accepted=True,
        )

    def terminate(self) -> RuntimeControlResult:
        self._target.terminate_runtime()
        return RuntimeControlResult(
            action="terminate",
            state=self._state(),
            accepted=True,
        )

    def status(self) -> RuntimeControlResult:
        return RuntimeControlResult(
            action="status",
            state=self._state(),
            accepted=True,
        )
