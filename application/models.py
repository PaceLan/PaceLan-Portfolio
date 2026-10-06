"""Application-layer domain models exposed to product interfaces."""

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, Tuple

from application.verification import VerificationResult


@dataclass(frozen=True)
class ProjectGoal:
    """Immutable application representation of a project's goal."""

    text: str = ""


@dataclass(frozen=True)
class ProjectModel:
    """Stable application representation of a project."""

    project_id: str
    goal: ProjectGoal = ProjectGoal()


@dataclass(frozen=True)
class TaskModel:
    """Stable application representation of a task."""

    task_id: str
    project_id: str
    description: str = ""
    context: str = ""


@dataclass(frozen=True)
class StepModel:
    """Stable application representation of a planned step."""

    step_id: str
    operation: str
    risk: str = "SAFE"
    approval: str = "NOT_REQUESTED"
    target: str = "."
    context: str | None = None
    readiness: str = "UNKNOWN"
    reason: str = ""
    ready: bool = False


@dataclass(frozen=True)
class PlanModel:
    """Stable application representation of a workflow plan."""

    task_id: str
    project_id: str
    steps: Tuple[StepModel, ...] = ()
    ready: bool = False
    issues: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()


@dataclass(frozen=True)
class RunModel:
    """Stable application representation of one execution run."""

    run_id: str
    task_id: str


@dataclass(frozen=True)
class ExecutionModel:
    """Stable application representation of execution state."""

    run_id: str
    status: str


@dataclass(frozen=True)
class ResultModel:
    """Stable application representation of execution results."""

    run_id: str
    status: str
    total_steps: int = 0
    successful_steps: int = 0
    failed_steps: int = 0
    blocked_steps: int = 0
    completed_successfully: bool = False
    failure_index: int | None = None


@dataclass(frozen=True)
class ProgressModel:
    """Stable application representation of plan/execution progress."""

    task_id: str
    completed_steps: int = 0
    total_steps: int = 0
    current_step_id: str | None = None

    def __post_init__(self) -> None:
        if self.completed_steps < 0:
            raise ValueError("completed_steps must be non-negative")
        if self.total_steps < 0:
            raise ValueError("total_steps must be non-negative")
        if self.completed_steps > self.total_steps:
            raise ValueError(
                "completed_steps must not exceed total_steps"
            )


@dataclass(frozen=True)
class SnapshotModel:
    """Stable application representation of an execution snapshot."""

    run_id: str
    task_id: str
    run_status: str
    step_states: Mapping[str, str] = ()
    current_step: str | None = None
    started_at: object | None = None
    finished_at: object | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "step_states",
            MappingProxyType(dict(self.step_states)),
        )


@dataclass(frozen=True)
class ApplicationExecutionModel:
    """Complete application-facing representation of one execution."""

    task: TaskModel
    plan: PlanModel
    run: RunModel
    result: ResultModel
    snapshot: SnapshotModel
    verification: VerificationResult | None = None