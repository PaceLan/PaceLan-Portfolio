from __future__ import annotations

from dataclasses import dataclass

from application.external_agent import (
    ExternalAgentRequest,
    ExternalAgentResponse,
    ExternalAgentStatus,
    ExternalConnectionReason,
    ExternalConnectionState,
)
from application.external_agent_transport import (
    ExternalAgentTransport,
    ExternalAgentTransportStatus,
    UnavailableExternalAgentTransport,
)
from application.universal_agent_interface import (
    AgentOperationRequest,
    UniversalAgentInterface,
)


@dataclass(frozen=True)
class ExternalGatewayResult:
    response: ExternalAgentResponse
    status: ExternalAgentStatus


class ExternalAgentGateway:
    """Application-owned gateway between external agents and UniversalAgent."""

    def __init__(
        self,
        agent: UniversalAgentInterface,
        *,
        workflow_id: str | None = None,
        transport: ExternalAgentTransport | None = None,
    ) -> None:
        if not isinstance(agent, UniversalAgentInterface):
            raise TypeError("agent must be a UniversalAgentInterface")

        self._agent = agent
        self._workflow_id = workflow_id
        self._transport = transport
        self._transport_status = (
            transport.status()
            if transport is not None
            else UnavailableExternalAgentTransport().status()
        )
        self._status = ExternalAgentStatus(
            state=ExternalConnectionState.DISCONNECTED,
        )

    @property
    def agent(self) -> UniversalAgentInterface:
        return self._agent

    @property
    def transport(self) -> ExternalAgentTransport | None:
        return self._transport

    def transport_status(self) -> ExternalAgentTransportStatus:
        return self._transport_status

    def status(self) -> ExternalAgentStatus:
        return self._status

    def connect(self) -> ExternalAgentStatus:
        if self._transport is None:
            self._status = ExternalAgentStatus(
                state=ExternalConnectionState.CONNECTED,
            )
            return self._status

        self._transport_status = self._transport.connect()

        if not self._transport_status.available:
            self._status = ExternalAgentStatus(
                state=ExternalConnectionState.DISCONNECTED,
                message=self._transport_status.message,
            )
            return self._status

        self._status = ExternalAgentStatus(
            state=ExternalConnectionState.CONNECTED,
            message=self._transport_status.message,
        )
        return self._status

    def disconnect(self) -> ExternalAgentStatus:
        if self._transport is not None:
            self._transport_status = self._transport.disconnect()

        self._status = ExternalAgentStatus(
            state=ExternalConnectionState.DISCONNECTED,
            message=self._transport_status.message,
        )
        return self._status

    def send(self, message: str) -> str:
        self._require_connected()

        if self._transport is None:
            raise RuntimeError("external Agent transport is not configured")

        return self._transport.send(message)

    def wait_external(
        self,
        reason: ExternalConnectionReason,
        *,
        message: str = "",
        recoverable: bool = True,
    ) -> ExternalAgentStatus:
        if reason is ExternalConnectionReason.NONE:
            raise ValueError("external waiting requires a reason")

        self._status = ExternalAgentStatus(
            state=ExternalConnectionState.WAITING_EXTERNAL,
            reason=reason,
            recoverable=recoverable,
            message=message,
        )
        return self._status

    def create_task(
        self,
        request: ExternalAgentRequest,
    ):
        self._require_connected()
        self._require_task_id(request)

        return self._agent.create_task(
            project_id=request.workflow_id or self._workflow_id or "external",
            description=request.payload,
            task_id=request.task_id,
        )

    def submit_task(
        self,
        request: ExternalAgentRequest,
        operations: tuple[AgentOperationRequest, ...] = (),
    ):
        self._require_connected()
        self._require_task_id(request)

        return self._agent.submit_task(
            request.task_id,
            operations,
        )

    def inspect_task(self, request: ExternalAgentRequest):
        self._require_task_id(request)
        return self._agent.inspect_task(request.task_id)

    def inspect_plan(self, request: ExternalAgentRequest):
        self._require_task_id(request)
        return self._agent.inspect_plan(request.task_id)

    def inspect_risk_approval(self, request: ExternalAgentRequest):
        self._require_task_id(request)
        return self._agent.inspect_risk_approval(request.task_id)

    def approve(
        self,
        request: ExternalAgentRequest,
        step_id: str,
        *,
        actor: str,
    ):
        self._require_connected()
        self._require_task_id(request)
        return self._agent.approve(
            request.task_id,
            step_id,
            actor=actor,
        )

    def reject(
        self,
        request: ExternalAgentRequest,
        step_id: str,
        *,
        actor: str,
    ):
        self._require_connected()
        self._require_task_id(request)
        return self._agent.reject(
            request.task_id,
            step_id,
            actor=actor,
        )

    def start(self, request: ExternalAgentRequest):
        self._require_connected()
        self._require_task_id(request)
        return self._agent.start(request.task_id)

    def pause(self, request: ExternalAgentRequest):
        self._require_connected()
        self._require_task_id(request)
        return self._agent.pause(request.task_id)

    def resume(self, request: ExternalAgentRequest):
        self._require_connected()
        self._require_task_id(request)
        return self._agent.resume(request.task_id)

    def stop(self, request: ExternalAgentRequest):
        self._require_connected()
        self._require_task_id(request)
        return self._agent.stop(request.task_id)

    def inspect_runtime(self):
        return self._agent.inspect_runtime()

    def inspect_execution(self, request: ExternalAgentRequest):
        return self._agent.inspect_execution(request.task_id)

    def result(self, request: ExternalAgentRequest):
        self._require_task_id(request)
        return self._agent.result(request.task_id)

    def history(self, *, limit: int = 100):
        return self._agent.history(limit=limit)

    def events(
        self,
        *,
        after_sequence: int = 0,
        task_id: str | None = None,
    ):
        return self._agent.events(
            after_sequence=after_sequence,
            task_id=task_id,
        )

    def make_response(
        self,
        request: ExternalAgentRequest,
        payload: str,
    ) -> ExternalAgentResponse:
        return ExternalAgentResponse(
            task_id=request.task_id,
            payload=payload,
            workflow_id=request.workflow_id or self._workflow_id,
        )

    def _require_connected(self) -> None:
        if self._status.state is not ExternalConnectionState.CONNECTED:
            raise RuntimeError("external Agent gateway is not connected")

    @staticmethod
    def _require_task_id(request: ExternalAgentRequest) -> None:
        if not request.task_id.strip():
            raise ValueError("task_id must not be empty")


__all__ = [
    "ExternalAgentGateway",
    "ExternalGatewayResult",
]
