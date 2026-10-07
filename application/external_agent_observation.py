"""External Agent observation layer for autonomous execution."""

from __future__ import annotations

from typing import Any, Mapping

from application.external_agent import (
    ExternalAgentRequest,
    ExternalAgentResponse,
    ExternalAgentStatus,
)
from application.observation_event import ObservationEvent


class ExternalAgentObservation:
    """Convert observed External Agent activity into ObservationEvent."""

    SOURCE = "external_agent"
    EVENT_TYPE = "external_agent"

    @classmethod
    def status(
        cls,
        status: ExternalAgentStatus,
        *,
        project_id: str | None = None,
        task_id: str | None = None,
        workflow_id: str | None = None,
        execution_id: str | None = None,
        correlation_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> ObservationEvent:
        if not isinstance(status, ExternalAgentStatus):
            raise TypeError("status must be an ExternalAgentStatus")

        event_payload: dict[str, Any] = {
            "reason": status.reason.value,
            "recoverable": status.recoverable,
            "message": status.message,
        }
        if payload:
            event_payload.update(dict(payload))

        return cls._event(
            observed_state=status.state.value,
            payload=event_payload,
            project_id=project_id,
            task_id=task_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            correlation_id=correlation_id,
        )

    @classmethod
    def request(
        cls,
        request: ExternalAgentRequest,
        *,
        command: str | None = None,
        project_id: str | None = None,
        execution_id: str | None = None,
        correlation_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> ObservationEvent:
        if not isinstance(request, ExternalAgentRequest):
            raise TypeError("request must be an ExternalAgentRequest")

        event_payload: dict[str, Any] = {
            "task_id": request.task_id,
            "workflow_id": request.workflow_id,
            "request_payload": request.payload,
        }
        if command is not None:
            event_payload["command"] = command
        if payload:
            event_payload.update(dict(payload))

        return cls._event(
            observed_state="REQUESTED",
            payload=event_payload,
            project_id=project_id,
            task_id=request.task_id,
            workflow_id=request.workflow_id,
            execution_id=execution_id,
            correlation_id=correlation_id,
        )

    @classmethod
    def response(
        cls,
        response: ExternalAgentResponse,
        *,
        command: str | None = None,
        project_id: str | None = None,
        execution_id: str | None = None,
        correlation_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
    ) -> ObservationEvent:
        if not isinstance(response, ExternalAgentResponse):
            raise TypeError("response must be an ExternalAgentResponse")

        event_payload: dict[str, Any] = {
            "task_id": response.task_id,
            "workflow_id": response.workflow_id,
            "response_payload": response.payload,
        }
        if command is not None:
            event_payload["command"] = command
        if payload:
            event_payload.update(dict(payload))

        return cls._event(
            observed_state="RESPONDED",
            payload=event_payload,
            project_id=project_id,
            task_id=response.task_id,
            workflow_id=response.workflow_id,
            execution_id=execution_id,
            correlation_id=correlation_id,
        )

    @classmethod
    def command(
        cls,
        *,
        command: str,
        task_id: str,
        workflow_id: str | None = None,
        project_id: str | None = None,
        execution_id: str | None = None,
        correlation_id: str | None = None,
        result: Any = None,
        payload: Mapping[str, Any] | None = None,
    ) -> ObservationEvent:
        if not isinstance(command, str) or not command.strip():
            raise ValueError("command must not be empty")
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id must not be empty")

        event_payload: dict[str, Any] = {
            "command": command,
            "task_id": task_id,
            "workflow_id": workflow_id,
            "result": result,
        }
        if payload:
            event_payload.update(dict(payload))

        return cls._event(
            observed_state="COMMAND",
            payload=event_payload,
            project_id=project_id,
            task_id=task_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            correlation_id=correlation_id,
        )

    @classmethod
    def _event(
        cls,
        *,
        observed_state: str,
        payload: Mapping[str, Any],
        project_id: str | None,
        task_id: str | None,
        workflow_id: str | None,
        execution_id: str | None,
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


__all__ = ["ExternalAgentObservation"]
