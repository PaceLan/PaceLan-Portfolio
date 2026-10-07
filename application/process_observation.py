"""Process observation layer for autonomous execution."""

from __future__ import annotations

from typing import Any, Mapping

from .observation_event import ObservationEvent
from .process_lifecycle import ProcessLifecycleState, ProcessSnapshot
from .process_lifecycle_controller import ProcessLifecycleController


class ProcessObservation:
    """Convert real process lifecycle observations into ObservationEvent."""

    SOURCE = "process"
    EVENT_TYPE = "process"

    def __init__(
        self,
        lifecycle: ProcessLifecycleController | None = None,
    ) -> None:
        self._lifecycle = lifecycle or ProcessLifecycleController()

    def snapshot(
        self,
        *,
        project_id: str | None = None,
        task_id: str | None = None,
        workflow_id: str | None = None,
        execution_id: str | None = None,
        correlation_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> ObservationEvent:
        process_snapshot = self._lifecycle.snapshot()
        return self.from_snapshot(
            process_snapshot,
            project_id=project_id,
            task_id=task_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            correlation_id=correlation_id,
            payload=payload,
        )

    @classmethod
    def from_snapshot(
        cls,
        snapshot: ProcessSnapshot,
        *,
        project_id: str | None = None,
        task_id: str | None = None,
        workflow_id: str | None = None,
        execution_id: str | None = None,
        correlation_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> ObservationEvent:
        if not isinstance(snapshot, ProcessSnapshot):
            raise TypeError("snapshot must be a ProcessSnapshot")

        event_payload: dict[str, Any] = {
            "process_id": snapshot.process_id,
            "exit_code": snapshot.exit_code,
            "started_at": snapshot.started_at,
            "finished_at": snapshot.finished_at,
        }
        if payload:
            event_payload.update(dict(payload))

        return ObservationEvent.create(
            event_type=cls.EVENT_TYPE,
            source=cls.SOURCE,
            observed_state=snapshot.state.value,
            payload=event_payload,
            project_id=project_id,
            task_id=task_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            correlation_id=correlation_id,
        )

    @classmethod
    def running(cls, snapshot: ProcessSnapshot, **context: Any) -> ObservationEvent:
        return cls._state_event(ProcessLifecycleState.RUNNING, snapshot, context)

    @classmethod
    def exited(cls, snapshot: ProcessSnapshot, **context: Any) -> ObservationEvent:
        return cls._state_event(ProcessLifecycleState.EXITED, snapshot, context)

    @classmethod
    def crashed(cls, snapshot: ProcessSnapshot, **context: Any) -> ObservationEvent:
        return cls._state_event(ProcessLifecycleState.CRASHED, snapshot, context)

    @classmethod
    def hung(cls, snapshot: ProcessSnapshot, **context: Any) -> ObservationEvent:
        return cls._state_event(ProcessLifecycleState.HUNG, snapshot, context)

    @classmethod
    def _state_event(
        cls,
        expected_state: ProcessLifecycleState,
        snapshot: ProcessSnapshot,
        context: Mapping[str, Any],
    ) -> ObservationEvent:
        if not isinstance(snapshot, ProcessSnapshot):
            raise TypeError("snapshot must be a ProcessSnapshot")
        if snapshot.state is not expected_state:
            raise ValueError(
                f"snapshot state must be {expected_state.value}"
            )
        return cls.from_snapshot(snapshot, **context)


__all__ = ["ProcessObservation"]
