from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from application.external_agent import (
    ExternalAgentRequest,
    ExternalAgentResponse,
)
from application.external_agent_gateway import ExternalAgentGateway
from application.universal_agent_interface import AgentOperationRequest


class ExternalAgentCommand(str, Enum):
    CREATE_TASK = "create_task"
    SUBMIT_TASK = "submit_task"
    INSPECT_TASK = "inspect_task"
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    RESULT = "result"


@dataclass(frozen=True)
class ExternalAgentBridgeResult:
    command: ExternalAgentCommand
    response: ExternalAgentResponse
    value: object | None = None


class ExternalAgentMessageBridge:
    """Map external commands onto the single existing Agent Gateway."""

    def __init__(self, gateway: ExternalAgentGateway) -> None:
        if not isinstance(gateway, ExternalAgentGateway):
            raise TypeError("gateway must be an ExternalAgentGateway")
        self._gateway = gateway

    @property
    def gateway(self) -> ExternalAgentGateway:
        return self._gateway

    def dispatch(
        self,
        request: ExternalAgentRequest,
        command: ExternalAgentCommand,
        *,
        operations: tuple[AgentOperationRequest, ...] = (),
    ) -> ExternalAgentBridgeResult:
        if not isinstance(request, ExternalAgentRequest):
            raise TypeError("request must be an ExternalAgentRequest")
        if not isinstance(command, ExternalAgentCommand):
            raise TypeError("command must be an ExternalAgentCommand")

        if command is ExternalAgentCommand.CREATE_TASK:
            value = self._gateway.create_task(request)
        elif command is ExternalAgentCommand.SUBMIT_TASK:
            value = self._gateway.submit_task(request, operations)
        elif command is ExternalAgentCommand.INSPECT_TASK:
            value = self._gateway.inspect_task(request)
        elif command is ExternalAgentCommand.START:
            value = self._gateway.start(request)
        elif command is ExternalAgentCommand.PAUSE:
            value = self._gateway.pause(request)
        elif command is ExternalAgentCommand.RESUME:
            value = self._gateway.resume(request)
        elif command is ExternalAgentCommand.STOP:
            value = self._gateway.stop(request)
        elif command is ExternalAgentCommand.RESULT:
            value = self._gateway.result(request)
        else:
            raise ValueError(f"unsupported external Agent command: {command}")

        return ExternalAgentBridgeResult(
            command=command,
            response=self._gateway.make_response(request, command.value),
            value=value,
        )


__all__ = [
    "ExternalAgentBridgeResult",
    "ExternalAgentCommand",
    "ExternalAgentMessageBridge",
]
