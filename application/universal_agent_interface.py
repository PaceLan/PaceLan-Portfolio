"""Transport-neutral, provider-independent local Agent interface."""

from __future__ import annotations

from collections import deque
from collections.abc import Callable, Mapping, Sequence
from concurrent.futures import Future
from dataclasses import dataclass, field, replace
from datetime import datetime, timezone
from enum import Enum
from threading import Lock, RLock
from types import MappingProxyType
from typing import Protocol
from uuid import uuid4

from application.task_context import TaskContext
from application.models import (
    ApplicationExecutionModel,
    PlanModel,
    ResultModel,
    SnapshotModel,
    StepModel,
    TaskModel,
)


class AgentTaskStatus(str, Enum):
    CREATED = "CREATED"
    SUBMITTED = "SUBMITTED"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    READY = "READY"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"
    STOPPED = "STOPPED"


class AgentRuntimeState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"
    UNKNOWN = "UNKNOWN"


class AgentEventName(str, Enum):
    TASK_CREATED = "task.created"
    TASK_SUBMITTED = "task.submitted"
    TASK_STARTED = "task.started"
    TASK_PAUSED = "task.paused"
    TASK_RESUMED = "task.resumed"
    TASK_WAITING_APPROVAL = "task.waiting_approval"
    TASK_APPROVED = "task.approved"
    TASK_REJECTED = "task.rejected"
    TASK_EXECUTION_STARTED = "task.execution_started"
    TASK_EXECUTION_PROGRESS = "task.execution_progress"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"
    TASK_STOPPED = "task.stopped"


@dataclass(frozen=True)
class AgentOperationRequest:
    """Serializable request for a locally registered operation capability."""

    operation: str
    target: str = "."
    context: str = ""

    def __post_init__(self) -> None:
        if not self.operation.strip():
            raise ValueError("operation must not be empty")


@dataclass(frozen=True)
class AgentUnderstandingView:
    task_id: str
    summary: str
    relevant_files: tuple[str, ...] = ()
    relevant_symbols: tuple[str, ...] = ()
    relationships: tuple[str, ...] = ()
    dependencies: tuple[str, ...] = ()


@dataclass(frozen=True)
class AgentRuntimeView:
    state: AgentRuntimeState
    accepted: bool
    message: str = ""


@dataclass(frozen=True)
class AgentExecutionView:
    run_id: str | None
    status: str
    progress: int
    current_step: str | None = None
    step_states: Mapping[str, str] = field(default_factory=dict)
    started_at: str | None = None
    finished_at: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "step_states",
            MappingProxyType(dict(self.step_states)),
        )


@dataclass(frozen=True)
class AgentTaskView:
    task: TaskModel
    status: AgentTaskStatus
    created_at: str
    plan: PlanModel | None = None
    understanding: AgentUnderstandingView | None = None
    execution: AgentExecutionView | None = None
    result: ResultModel | None = None
    error: str | None = None


@dataclass(frozen=True)
class AgentEvent:
    sequence: int
    name: AgentEventName
    task_id: str
    timestamp: str
    payload: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "payload", MappingProxyType(dict(self.payload)))


class AgentExecutionBackend(Protocol):
    """Local execution adapter; transport and model providers stay outside."""

    def risk_for(self, operation: str) -> str: ...

    def start(
        self,
        task: TaskModel,
        operations: tuple[AgentOperationRequest, ...],
        plan: PlanModel,
        progress: Callable[[str, str], None],
    ) -> Future[ApplicationExecutionModel]: ...

    def pause(self) -> AgentRuntimeView: ...

    def resume(self) -> AgentRuntimeView: ...

    def stop(self) -> AgentRuntimeView: ...

    def inspect_runtime(self) -> AgentRuntimeView: ...


class UnderstandingProvider(Protocol):
    def inspect(self, task: TaskModel) -> AgentUnderstandingView | None: ...


class ApprovalAuthorizer(Protocol):
    def authorize(
        self,
        task_id: str,
        step_id: str,
        decision: str,
        actor: str,
    ) -> bool: ...


@dataclass
class _TaskRecord:
    task: TaskModel
    status: AgentTaskStatus
    created_at: str
    operations: tuple[AgentOperationRequest, ...] = ()
    plan: PlanModel | None = None
    understanding: AgentUnderstandingView | None = None
    execution: ApplicationExecutionModel | None = None
    result: ResultModel | None = None
    error: str | None = None
    progress: int = 0
    completed_step_ids: set[str] = field(default_factory=set)
    current_step: str | None = None
    step_states: dict[str, str] = field(default_factory=dict)
    future: Future[ApplicationExecutionModel] | None = None


class UniversalAgentInterface:
    """Application-owned Agent API with explicit task and approval state."""

    def __init__(
        self,
        backend: AgentExecutionBackend,
        *,
        approval_authorizer: ApprovalAuthorizer | None = None,
        understanding_provider: UnderstandingProvider | None = None,
        max_operations_per_task: int = 32,
        max_retained_events: int = 5000,
    ) -> None:
        if max_operations_per_task < 1:
            raise ValueError("max_operations_per_task must be positive")
        if max_retained_events < 1:
            raise ValueError("max_retained_events must be positive")
        self._backend = backend
        self._approval_authorizer = approval_authorizer
        self._understanding_provider = understanding_provider
        self.max_operations_per_task = max_operations_per_task
        self._tasks: dict[str, _TaskRecord] = {}
        self._events: deque[AgentEvent] = deque(maxlen=max_retained_events)
        self._event_sequence = 0
        self._active_task_id: str | None = None
        self._lock = RLock()

    def create_task(
        self,
        project_id: str,
        description: str,
        context: str = "",
        *,
        task_id: str | None = None,
    ) -> AgentTaskView:
        if not project_id.strip():
            raise ValueError("project_id must not be empty")
        if not description.strip():
            raise ValueError("description must not be empty")

        identifier = task_id or uuid4().hex
        task = TaskModel(
            task_id=identifier,
            project_id=project_id,
            description=description,
            context=context,
        )
        with self._lock:
            if identifier in self._tasks:
                raise ValueError(f"task already exists: {identifier}")
            record = _TaskRecord(
                task=task,
                status=AgentTaskStatus.CREATED,
                created_at=self._now(),
            )
            self._tasks[identifier] = record
            self._emit(AgentEventName.TASK_CREATED, identifier)
            return self._view(record)

    def submit_task(
        self,
        task_id: str,
        operations: Sequence[AgentOperationRequest] = (),
    ) -> AgentTaskView:
        requested = tuple(operations)
        if len(requested) > self.max_operations_per_task:
            raise PermissionError("task exceeds the operation limit")
        if not all(isinstance(item, AgentOperationRequest) for item in requested):
            raise TypeError("operations must be AgentOperationRequest values")

        with self._lock:
            record = self._require_task(task_id)
            if record.status is not AgentTaskStatus.CREATED:
                raise RuntimeError("only a new task can be submitted")

            steps: list[StepModel] = []
            for index, operation in enumerate(requested, start=1):
                risk = self._backend.risk_for(operation.operation).upper()
                if risk not in {"SAFE", "NOTABLE", "HIGH_RISK"}:
                    raise ValueError(f"unsupported operation risk: {risk}")
                step_id = f"{task_id}-step-{index:03d}"
                waiting = risk == "HIGH_RISK"
                steps.append(
                    StepModel(
                        step_id=step_id,
                        operation=operation.operation,
                        risk=risk,
                        approval="NOT_REQUESTED",
                        target=operation.target,
                        context=operation.context or None,
                        readiness="BLOCKED" if waiting else "READY",
                        reason=(
                            "high-risk step requires explicit approval"
                            if waiting
                            else "risk policy permits execution"
                        ),
                        ready=not waiting,
                    )
                )

            pending = tuple(step for step in steps if not step.ready)
            record.operations = requested
            record.plan = PlanModel(
                task_id=record.task.task_id,
                project_id=record.task.project_id,
                steps=tuple(steps),
                ready=not pending,
                issues=tuple(step.reason for step in pending),
            )
            record.status = (
                AgentTaskStatus.WAITING_APPROVAL
                if pending
                else AgentTaskStatus.READY
            )
            self._emit(
                AgentEventName.TASK_SUBMITTED,
                task_id,
                operation_count=len(requested),
            )
            if pending:
                self._emit(
                    AgentEventName.TASK_WAITING_APPROVAL,
                    task_id,
                    step_ids=tuple(step.step_id for step in pending),
                )
            return self._view(record)

    def task_context(
        self,
        task_id: str,
        *,
        workflow_id: str | None = None,
    ) -> TaskContext:
        with self._lock:
            record = self._require_task(task_id)
            return TaskContext(
                project_id=record.task.project_id,
                task_id=record.task.task_id,
                workflow_id=workflow_id,
            )

    def inspect_task(self, task_id: str) -> AgentTaskView:
        with self._lock:
            return self._view(self._require_task(task_id))

    def inspect_understanding(
        self,
        task_id: str,
    ) -> AgentUnderstandingView | None:
        with self._lock:
            record = self._require_task(task_id)
            if record.understanding is not None:
                return record.understanding
            provider = self._understanding_provider
            task = record.task
        if provider is None:
            return None
        understanding = provider.inspect(task)
        if understanding is not None and not isinstance(
            understanding,
            AgentUnderstandingView,
        ):
            raise TypeError("understanding provider returned an invalid value")
        with self._lock:
            record.understanding = understanding
            return understanding

    def inspect_plan(self, task_id: str) -> PlanModel | None:
        return self.inspect_task(task_id).plan

    def inspect_risk_approval(self, task_id: str) -> tuple[StepModel, ...]:
        plan = self.inspect_plan(task_id)
        return () if plan is None else plan.steps

    def approve(self, task_id: str, step_id: str, *, actor: str) -> AgentTaskView:
        self._authorize(task_id, step_id, "approve", actor)
        with self._lock:
            record = self._require_task(task_id)
            step = self._require_step(record, step_id)
            if step.risk != "HIGH_RISK":
                raise ValueError("explicit approval is only valid for high-risk steps")
            updated = replace(
                step,
                approval="APPROVED",
                readiness="READY",
                reason="approved by authorized reviewer",
                ready=True,
            )
            self._replace_step(record, updated)
            pending = tuple(item for item in record.plan.steps if not item.ready)
            record.plan = replace(
                record.plan,
                ready=not pending,
                issues=tuple(item.reason for item in pending),
            )
            if not pending:
                record.status = AgentTaskStatus.READY
            self._emit(
                AgentEventName.TASK_APPROVED,
                task_id,
                step_id=step_id,
                actor=actor,
            )
            return self._view(record)

    def reject(self, task_id: str, step_id: str, *, actor: str) -> AgentTaskView:
        self._authorize(task_id, step_id, "reject", actor)
        with self._lock:
            record = self._require_task(task_id)
            step = self._require_step(record, step_id)
            if step.risk != "HIGH_RISK":
                raise ValueError("explicit rejection is only valid for high-risk steps")
            self._replace_step(
                record,
                replace(
                    step,
                    approval="DENIED",
                    readiness="BLOCKED",
                    reason="rejected by authorized reviewer",
                    ready=False,
                ),
            )
            record.plan = replace(
                record.plan,
                ready=False,
                issues=tuple(
                    item.reason for item in record.plan.steps if not item.ready
                ),
            )
            record.status = AgentTaskStatus.REJECTED
            self._emit(
                AgentEventName.TASK_REJECTED,
                task_id,
                step_id=step_id,
                actor=actor,
            )
            return self._view(record)

    def start(self, task_id: str) -> AgentTaskView:
        with self._lock:
            record = self._require_task(task_id)
            if record.status is not AgentTaskStatus.READY or record.plan is None:
                raise PermissionError("task is not ready for execution")
            if self._active_task_id is not None:
                raise RuntimeError("another Agent task is active")
            self._active_task_id = task_id
            record.status = AgentTaskStatus.RUNNING
            task = record.task
            operations = record.operations
            plan = record.plan

        progress_lock = Lock()
        pending_progress: list[tuple[str, str]] = []
        start_events_published = False

        def on_progress(step_id: str, state: str) -> None:
            with progress_lock:
                if not start_events_published:
                    pending_progress.append((step_id, state))
                    return
                self._on_progress(task_id, step_id, state)

        try:
            future = self._backend.start(
                task,
                operations,
                plan,
                on_progress,
            )
        except Exception:
            with self._lock:
                record.status = AgentTaskStatus.READY
                self._active_task_id = None
            raise

        with progress_lock:
            with self._lock:
                record.future = future
                self._emit(AgentEventName.TASK_STARTED, task_id)
                self._emit(AgentEventName.TASK_EXECUTION_STARTED, task_id)
                view = self._view(record)
                start_events_published = True
                queued = tuple(pending_progress)
                pending_progress.clear()
            for step_id, state in queued:
                self._on_progress(task_id, step_id, state)
        future.add_done_callback(
            lambda completed: self._complete(task_id, completed)
        )
        return view

    def pause(self, task_id: str) -> AgentRuntimeView:
        with self._lock:
            self._require_active(task_id, AgentTaskStatus.RUNNING)
        runtime = self._backend.pause()
        with self._lock:
            record = self._require_task(task_id)
            record.status = AgentTaskStatus.PAUSED
            self._emit(AgentEventName.TASK_PAUSED, task_id)
        return runtime

    def resume(self, task_id: str) -> AgentRuntimeView:
        with self._lock:
            self._require_active(task_id, AgentTaskStatus.PAUSED)
        runtime = self._backend.resume()
        with self._lock:
            record = self._require_task(task_id)
            record.status = AgentTaskStatus.RUNNING
            self._emit(AgentEventName.TASK_RESUMED, task_id)
        return runtime

    def stop(self, task_id: str) -> AgentRuntimeView:
        with self._lock:
            record = self._require_task(task_id)
            if self._active_task_id != task_id or record.status not in {
                AgentTaskStatus.RUNNING,
                AgentTaskStatus.PAUSED,
            }:
                raise RuntimeError("task is not active")
        runtime = self._backend.stop()
        with self._lock:
            record.status = AgentTaskStatus.STOPPED
            self._active_task_id = None
            self._emit(AgentEventName.TASK_STOPPED, task_id)
        return runtime

    def inspect_runtime(self) -> AgentRuntimeView:
        return self._backend.inspect_runtime()

    def inspect_execution(self, task_id: str) -> AgentExecutionView:
        with self._lock:
            record = self._require_task(task_id)
            if record.execution is None:
                return AgentExecutionView(
                    run_id=None,
                    status=record.status.value,
                    progress=record.progress,
                    current_step=record.current_step,
                    step_states=record.step_states,
                )
            snapshot = record.execution.snapshot
            progress = self._snapshot_progress(snapshot)
            return AgentExecutionView(
                run_id=record.execution.run.run_id,
                status=snapshot.run_status,
                progress=progress,
                current_step=snapshot.current_step,
                step_states=snapshot.step_states,
                started_at=self._time_text(snapshot.started_at),
                finished_at=self._time_text(snapshot.finished_at),
            )

    def inspect_progress(self, task_id: str) -> int:
        with self._lock:
            return self._require_task(task_id).progress

    def result(self, task_id: str) -> ResultModel | None:
        with self._lock:
            return self._require_task(task_id).result

    def history(self, *, limit: int = 100) -> tuple[AgentTaskView, ...]:
        if limit < 1:
            raise ValueError("limit must be positive")
        with self._lock:
            records = tuple(self._tasks.values())[-limit:]
            return tuple(self._view(record) for record in reversed(records))

    def events(
        self,
        *,
        after_sequence: int = 0,
        task_id: str | None = None,
    ) -> tuple[AgentEvent, ...]:
        with self._lock:
            return tuple(
                event
                for event in self._events
                if event.sequence > after_sequence
                and (task_id is None or event.task_id == task_id)
            )

    def _on_progress(self, task_id: str, step_id: str, state: str) -> None:
        with self._lock:
            record = self._require_task(task_id)
            normalized_state = state.strip().upper()
            record.step_states[step_id] = normalized_state
            if normalized_state in {"COMPLETED", "FAILED"}:
                record.completed_step_ids.add(step_id)
            if normalized_state == "STARTED":
                record.current_step = step_id
            elif record.current_step == step_id:
                record.current_step = None
            total = len(record.operations)
            record.progress = (
                100
                if total == 0
                else int(len(record.completed_step_ids) * 100 / total)
            )
            self._emit(
                AgentEventName.TASK_EXECUTION_PROGRESS,
                task_id,
                step_id=step_id,
                state=state,
                progress=record.progress,
            )

    def _complete(
        self,
        task_id: str,
        future: Future[ApplicationExecutionModel],
    ) -> None:
        try:
            execution = future.result()
            if not isinstance(execution, ApplicationExecutionModel):
                raise TypeError("execution backend returned an invalid result")
        except Exception as error:
            with self._lock:
                record = self._require_task(task_id)
                record.error = str(error)
                if record.status is not AgentTaskStatus.STOPPED:
                    record.status = AgentTaskStatus.FAILED
                    self._emit(
                        AgentEventName.TASK_FAILED,
                        task_id,
                        error=str(error),
                    )
                self._active_task_id = None
            return

        with self._lock:
            record = self._require_task(task_id)
            record.execution = execution
            record.result = execution.result
            if record.status is AgentTaskStatus.STOPPED:
                self._active_task_id = None
                return
            failed = (
                execution.result.failed_steps > 0
                or execution.result.blocked_steps > 0
                or execution.result.status.upper() in {"FAILED", "BLOCKED"}
            )
            record.progress = self._snapshot_progress(execution.snapshot)
            if not record.operations:
                record.progress = 100
            if failed:
                record.status = AgentTaskStatus.FAILED
                self._emit(
                    AgentEventName.TASK_FAILED,
                    task_id,
                    result_status=execution.result.status,
                )
            else:
                record.status = AgentTaskStatus.COMPLETED
                self._emit(
                    AgentEventName.TASK_COMPLETED,
                    task_id,
                    result_status=execution.result.status,
                )
            self._emit(
                AgentEventName.TASK_EXECUTION_PROGRESS,
                task_id,
                progress=record.progress,
            )
            self._active_task_id = None

    def _authorize(
        self,
        task_id: str,
        step_id: str,
        decision: str,
        actor: str,
    ) -> None:
        if not actor.strip():
            raise ValueError("actor must not be empty")
        authorizer = self._approval_authorizer
        if authorizer is None or not authorizer.authorize(
            task_id,
            step_id,
            decision,
            actor,
        ):
            raise PermissionError("approval decision is not authorized")

    def _require_active(
        self,
        task_id: str,
        expected_status: AgentTaskStatus,
    ) -> None:
        record = self._require_task(task_id)
        if self._active_task_id != task_id or record.status is not expected_status:
            raise RuntimeError("task runtime state does not allow this action")

    def _require_task(self, task_id: str) -> _TaskRecord:
        try:
            return self._tasks[task_id]
        except KeyError as error:
            raise KeyError(f"unknown task: {task_id}") from error

    @staticmethod
    def _require_step(record: _TaskRecord, step_id: str) -> StepModel:
        if record.plan is None:
            raise RuntimeError("task has no submitted plan")
        for step in record.plan.steps:
            if step.step_id == step_id:
                return step
        raise KeyError(f"unknown plan step: {step_id}")

    @staticmethod
    def _replace_step(record: _TaskRecord, updated: StepModel) -> None:
        if record.plan is None:
            raise RuntimeError("task has no submitted plan")
        record.plan = replace(
            record.plan,
            steps=tuple(
                updated if step.step_id == updated.step_id else step
                for step in record.plan.steps
            ),
        )

    def _view(self, record: _TaskRecord) -> AgentTaskView:
        execution = AgentExecutionView(
            run_id=None,
            status=record.status.value,
            progress=record.progress,
            current_step=record.current_step,
            step_states=record.step_states,
        )
        if record.execution is not None:
            snapshot = record.execution.snapshot
            execution = AgentExecutionView(
                run_id=record.execution.run.run_id,
                status=snapshot.run_status,
                progress=self._snapshot_progress(snapshot),
                current_step=snapshot.current_step,
                step_states=snapshot.step_states,
                started_at=self._time_text(snapshot.started_at),
                finished_at=self._time_text(snapshot.finished_at),
            )
        return AgentTaskView(
            task=record.task,
            status=record.status,
            created_at=record.created_at,
            plan=record.plan,
            understanding=record.understanding,
            execution=execution,
            result=record.result,
            error=record.error,
        )

    def _emit(
        self,
        name: AgentEventName,
        task_id: str,
        **payload: object,
    ) -> AgentEvent:
        self._event_sequence += 1
        event = AgentEvent(
            sequence=self._event_sequence,
            name=name,
            task_id=task_id,
            timestamp=self._now(),
            payload=payload,
        )
        self._events.append(event)
        return event

    @staticmethod
    def _snapshot_progress(snapshot: SnapshotModel) -> int:
        statuses = tuple(
            str(getattr(status, "value", status)).upper()
            for status in snapshot.step_states.values()
        )
        if not statuses:
            return 100 if snapshot.finished_at is not None else 0
        completed = sum(
            status in {"SUCCESS", "FAILED", "SKIPPED", "BLOCKED"}
            for status in statuses
        )
        return int(completed * 100 / len(statuses))

    @staticmethod
    def _time_text(value) -> str | None:
        return value.isoformat() if value is not None else None

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


__all__ = [
    "AgentEvent",
    "AgentEventName",
    "AgentExecutionBackend",
    "AgentExecutionView",
    "AgentOperationRequest",
    "AgentRuntimeState",
    "AgentRuntimeView",
    "AgentTaskStatus",
    "AgentTaskView",
    "AgentUnderstandingView",
    "ApprovalAuthorizer",
    "UnderstandingProvider",
    "UniversalAgentInterface",
]
