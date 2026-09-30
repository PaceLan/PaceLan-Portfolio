"""Presentation-layer loading and progress state for M22.3."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ProgressMode(str, Enum):
    IDLE = "idle"
    LOADING = "loading"
    PROCESSING = "processing"
    INDETERMINATE = "indeterminate"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass(frozen=True)
class ProgressState:
    mode: ProgressMode = ProgressMode.IDLE
    progress: int = 0
    current_step: str | None = None
    completed_steps: int = 0
    total_steps: int = 0
    message: str = ""

    def __post_init__(self) -> None:
        if not 0 <= self.progress <= 100:
            raise ValueError("progress must be between 0 and 100")
        if self.completed_steps < 0:
            raise ValueError("completed_steps must be non-negative")
        if self.total_steps < 0:
            raise ValueError("total_steps must be non-negative")
        if self.total_steps and self.completed_steps > self.total_steps:
            raise ValueError("completed_steps must not exceed total_steps")


class ProgressMapper:
    """Maps real Agent execution state to presentation progress."""

    @staticmethod
    def from_execution(execution) -> ProgressState:
        if execution is None:
            return ProgressState()

        status = str(getattr(execution, "status", "Idle")).upper()
        progress = int(getattr(execution, "progress", 0) or 0)
        current_step = getattr(execution, "current_step", None)
        step_states = tuple(getattr(execution, "step_states", ()) or ())

        completed = sum(
            1
            for state in step_states
            if str(state).upper()
            in {"SUCCESS", "FAILED", "SKIPPED", "COMPLETED"}
        )
        total = len(step_states)

        if status in {"FAILED", "FAILURE", "ERROR"}:
            mode = ProgressMode.FAILED
        elif status in {"SUCCESS", "COMPLETED", "COMPLETE"}:
            mode = ProgressMode.COMPLETE
            progress = 100
        elif status in {
            "IN_PROGRESS",
            "RUNNING",
            "PROCESSING",
            "EXECUTING",
        }:
            mode = ProgressMode.PROCESSING
        elif current_step is not None or total:
            mode = ProgressMode.LOADING
        else:
            mode = ProgressMode.IDLE

        return ProgressState(
            mode=mode,
            progress=max(0, min(100, progress)),
            current_step=current_step,
            completed_steps=completed,
            total_steps=total,
            message=str(getattr(execution, "status", "") or ""),
        )


__all__ = ["ProgressMode", "ProgressState", "ProgressMapper"]