"""Immutable Agent interaction state models for the UI layer."""

from dataclasses import dataclass

from application.models import (
    PlanModel,
    ResultModel,
    RunModel,
    SnapshotModel,
    TaskModel,
)


@dataclass(frozen=True)
class AgentTaskState:
    """Current Agent task presentation state."""

    title: str = "No task"
    description: str = "No task selected"
    status: str = "No task"


@dataclass(frozen=True)
class AgentPlanState:
    """Current Agent plan presentation state."""

    summary: str = "No plan available"
    status: str = "No plan"
    steps: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentUnderstandingState:
    """Current Agent context-understanding presentation state."""

    summary: str = "No understanding available"
    relevant_files: tuple[str, ...] = ()
    relevant_symbols: tuple[str, ...] = ()
    relationships: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentRiskApprovalStepState:
    """Presentation state for one workflow step safety assessment."""

    step_id: str
    risk: str
    approval: str
    readiness: str
    reason: str
    ready: bool


@dataclass(frozen=True)
class AgentRiskApprovalState:
    """Presentation state for workflow risk and approval readiness."""

    ready: bool = False
    steps: tuple[AgentRiskApprovalStepState, ...] = ()
    issues: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentExecutionState:
    """Current Agent execution presentation state."""

    status: str = "Idle"
    run_id: str = ""
    current_step: str | None = None
    step_states: tuple[str, ...] = ()
    progress: int = 0
    failure_reason: str = ""
    started_at: str = ""
    finished_at: str = ""


@dataclass(frozen=True)
class AgentResultState:
    """Current Agent result presentation state."""

    summary: str = "No result available"
    status: str = "No result"


@dataclass(frozen=True)
class AgentHistoryEntry:
    """Immutable record of one real Agent execution."""

    task: TaskModel
    plan: PlanModel
    run: RunModel
    result: ResultModel
    snapshot: SnapshotModel

    @property
    def run_id(self) -> str:
        return self.run.run_id


@dataclass(frozen=True)
class AgentHistoryState:
    """Immutable presentation state for historical Agent executions."""

    entries: tuple[AgentHistoryEntry, ...] = ()
    selected_run_id: str | None = None
    status: str = "Empty"


@dataclass(frozen=True)
class AgentInteractionState:
    """Immutable presentation state for the Agent interaction panel."""

    task: AgentTaskState = AgentTaskState()
    understanding: AgentUnderstandingState = AgentUnderstandingState()
    plan: AgentPlanState = AgentPlanState()
    risk_approval: AgentRiskApprovalState = AgentRiskApprovalState()
    execution: AgentExecutionState = AgentExecutionState()
    result: AgentResultState = AgentResultState()
    history: AgentHistoryState = AgentHistoryState()


__all__ = [
    "AgentTaskState",
    "AgentPlanState",
    "AgentUnderstandingState",
    "AgentRiskApprovalStepState",
    "AgentRiskApprovalState",
    "AgentExecutionState",
    "AgentResultState",
    "AgentHistoryEntry",
    "AgentHistoryState",
    "AgentInteractionState",
]
