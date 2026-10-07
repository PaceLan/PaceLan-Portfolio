from __future__ import annotations

from typing import Any, Mapping

from application.execution_context import ExecutionContext
from application.models import ExecutionModel, ResultModel
from application.observation_event import ObservationEvent


class ExecutionObservation:
    """Convert real execution state and result models into observation events."""

    SOURCE = "execution"
    EVENT_TYPE = "execution"

    @classmethod
    def context(
        cls,
        context: ExecutionContext,
        *,
        correlation_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> ObservationEvent:
        if not isinstance(context, ExecutionContext):
            raise TypeError("context must be an ExecutionContext")

        event_payload = {
            "run_id": context.run_id,
            "step_id": context.step_id,
            "command_id": context.command_id,
            "process_id": context.process_id,
            "process_state": context.process_state,
            "terminal_id": context.terminal_id,
            "terminal_session_id": context.terminal_session_id,
            "terminal_state": context.terminal_state,
            "recoverability": context.recoverability,
            **dict(payload or {}),
        }

        return cls._event(
            observed_state=context.execution_state,
            payload=event_payload,
            project_id=context.project_id,
            task_id=context.task_id,
            workflow_id=context.workflow_id,
            execution_id=context.run_id,
            correlation_id=correlation_id,
        )

    @classmethod
    def execution(
        cls,
        execution: ExecutionModel,
        *,
        task_id: str | None = None,
        project_id: str | None = None,
        workflow_id: str | None = None,
        correlation_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> ObservationEvent:
        if not isinstance(execution, ExecutionModel):
            raise TypeError("execution must be an ExecutionModel")

        event_payload = {
            "run_id": execution.run_id,
            **dict(payload or {}),
        }

        return cls._event(
            observed_state=execution.status,
            payload=event_payload,
            project_id=project_id,
            task_id=task_id,
            workflow_id=workflow_id,
            execution_id=execution.run_id,
            correlation_id=correlation_id,
        )

    @classmethod
    def result(
        cls,
        result: ResultModel,
        *,
        task_id: str | None = None,
        project_id: str | None = None,
        workflow_id: str | None = None,
        correlation_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> ObservationEvent:
        if not isinstance(result, ResultModel):
            raise TypeError("result must be a ResultModel")

        event_payload = {
            "run_id": result.run_id,
            "total_steps": result.total_steps,
            "successful_steps": result.successful_steps,
            "failed_steps": result.failed_steps,
            "blocked_steps": result.blocked_steps,
            "completed_successfully": result.completed_successfully,
            "failure_index": result.failure_index,
            **dict(payload or {}),
        }

        return cls._event(
            observed_state=result.status,
            payload=event_payload,
            project_id=project_id,
            task_id=task_id,
            workflow_id=workflow_id,
            execution_id=result.run_id,
            correlation_id=correlation_id,
        )

    @classmethod
    def started(cls, context: ExecutionContext, **kwargs: Any) -> ObservationEvent:
        return cls._state(context, "STARTED", **kwargs)

    @classmethod
    def running(cls, context: ExecutionContext, **kwargs: Any) -> ObservationEvent:
        return cls._state(context, "RUNNING", **kwargs)

    @classmethod
    def paused(cls, context: ExecutionContext, **kwargs: Any) -> ObservationEvent:
        return cls._state(context, "PAUSED", **kwargs)

    @classmethod
    def stopped(cls, context: ExecutionContext, **kwargs: Any) -> ObservationEvent:
        return cls._state(context, "STOPPED", **kwargs)

    @classmethod
    def completed(cls, context: ExecutionContext, **kwargs: Any) -> ObservationEvent:
        return cls._state(context, "COMPLETED", **kwargs)

    @classmethod
    def failed(cls, context: ExecutionContext, **kwargs: Any) -> ObservationEvent:
        return cls._state(context, "FAILED", **kwargs)

    @classmethod
    def _state(
        cls,
        context: ExecutionContext,
        state: str,
        **kwargs: Any,
    ) -> ObservationEvent:
        return cls.context(context, payload={"state_event": state, **kwargs})

    @classmethod
    def _event(
        cls,
        *,
        observed_state: str,
        payload: Mapping[str, Any],
        project_id: str | None,
        task_id: str | None,
        workflow_id: str | None,
        execution_id: str,
        correlation_id: str | None,
    ) -> ObservationEvent:
        return ObservationEvent.create(
            event_type=cls.EVENT_TYPE,
            source=cls.SOURCE,
            observed_state=observed_state,
            payload=payload,
            project_id=project_id,
            task_id=task_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            correlation_id=correlation_id,
        )


__all__ = ["ExecutionObservation"]
