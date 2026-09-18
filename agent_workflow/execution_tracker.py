from datetime import datetime, timezone
from types import MappingProxyType
from typing import Mapping

from agent_workflow.execution_tracking import RunStatus, StepStatus
from agent_workflow.workflow_run import WorkflowRunContext


class ExecutionTracker:
    """Track the lifecycle state of one workflow run and its steps."""

    def __init__(
        self,
        context: WorkflowRunContext,
        step_ids: tuple[str, ...],
    ) -> None:
        if not isinstance(step_ids, tuple):
            step_ids = tuple(step_ids)

        for step_id in step_ids:
            if not isinstance(step_id, str) or not step_id:
                raise ValueError("step_ids must contain non-empty strings")

        if len(step_ids) != len(set(step_ids)):
            raise ValueError("step_ids must not contain duplicates")

        self._context = context
        self._run_status = RunStatus.CREATED
        self._step_states = {
            step_id: StepStatus.PENDING
            for step_id in step_ids
        }
        self._current_step: str | None = None
        self._started_at: datetime | None = None
        self._finished_at: datetime | None = None

    @property
    def context(self) -> WorkflowRunContext:
        return self._context

    @property
    def run_status(self) -> RunStatus:
        return self._run_status

    @property
    def step_states(self) -> Mapping[str, StepStatus]:
        return MappingProxyType(self._step_states)

    @property
    def current_step(self) -> str | None:
        return self._current_step

    @property
    def started_at(self) -> datetime | None:
        return self._started_at

    @property
    def finished_at(self) -> datetime | None:
        return self._finished_at

    def snapshot(self) -> "ExecutionSnapshot":
        from agent_workflow.execution_snapshot import ExecutionSnapshot

        return ExecutionSnapshot(
            run_id=self._context.run_id,
            task_id=self._context.task_id,
            run_status=self._run_status,
            step_states=self._step_states,
            current_step=self._current_step,
            started_at=self._started_at,
            finished_at=self._finished_at,
        )

    def start_run(self) -> None:
        self._require_run_status(RunStatus.CREATED)
        self._run_status = RunStatus.RUNNING
        self._started_at = datetime.now(timezone.utc)
        self._finished_at = None

    def start_step(self, step_id: str) -> None:
        self._require_step_exists(step_id)
        self._require_run_status(RunStatus.RUNNING)
        if self._current_step is not None:
            raise RuntimeError("another step is already running")
        if self._step_states[step_id] is not StepStatus.PENDING:
            raise RuntimeError("step is not pending")
        self._step_states[step_id] = StepStatus.RUNNING
        self._current_step = step_id

    def complete_step(self, step_id: str) -> None:
        self._require_step_exists(step_id)
        self._require_run_status(RunStatus.RUNNING)
        if self._step_states[step_id] is not StepStatus.RUNNING:
            raise RuntimeError("step is not running")
        self._step_states[step_id] = StepStatus.SUCCESS
        self._current_step = None

    def fail_step(self, step_id: str) -> None:
        self._require_step_exists(step_id)
        self._require_run_status(RunStatus.RUNNING)
        if self._step_states[step_id] is not StepStatus.RUNNING:
            raise RuntimeError("step is not running")
        self._step_states[step_id] = StepStatus.FAILED
        self._current_step = None

    def skip_step(self, step_id: str) -> None:
        self._require_step_exists(step_id)
        self._require_run_status(RunStatus.RUNNING)
        if self._step_states[step_id] is not StepStatus.PENDING:
            raise RuntimeError("step is not pending")
        self._step_states[step_id] = StepStatus.SKIPPED

    def complete_run(self) -> None:
        self._require_run_status(RunStatus.RUNNING)
        if self._current_step is not None:
            raise RuntimeError("cannot complete run while a step is running")
        self._run_status = RunStatus.COMPLETED
        self._finished_at = datetime.now(timezone.utc)
        self._current_step = None

    def fail_run(self) -> None:
        self._require_run_status(RunStatus.RUNNING)
        if self._current_step is not None:
            raise RuntimeError("cannot fail run while a step is running")
        self._run_status = RunStatus.FAILED
        self._finished_at = datetime.now(timezone.utc)
        self._current_step = None

    def _require_run_status(self, expected: RunStatus) -> None:
        if self._run_status is not expected:
            raise RuntimeError(
                f"invalid run transition from {self._run_status.value}"
            )

    def _require_step_exists(self, step_id: str) -> None:
        if step_id not in self._step_states:
            raise KeyError(step_id)
