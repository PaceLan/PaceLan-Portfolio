from dataclasses import dataclass
from datetime import datetime
from types import MappingProxyType
from typing import Mapping

from agent_workflow.execution_tracking import RunStatus, StepStatus


@dataclass(frozen=True)
class ExecutionSnapshot:
    """Immutable observation of one workflow run's execution state."""

    run_id: str
    task_id: str
    run_status: RunStatus
    step_states: Mapping[str, StepStatus]
    current_step: str | None
    started_at: datetime | None
    finished_at: datetime | None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "step_states",
            MappingProxyType(dict(self.step_states)),
        )