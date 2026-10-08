from __future__ import annotations

from application.runtime_control import (
    ApplicationRuntimeControlService,
    RuntimeControlResult,
)
from application.universal_agent_interface import UniversalAgentInterface
from application.universal_agent_runtime_target import (
    UniversalAgentRuntimeTarget,
)


class AgentRuntimeControlService:
    """Application-facing runtime controls for one Agent task."""

    def __init__(
        self,
        agent: UniversalAgentInterface,
        task_id: str,
    ) -> None:
        self._control = ApplicationRuntimeControlService(
            UniversalAgentRuntimeTarget(agent, task_id)
        )

    def start(self) -> RuntimeControlResult:
        return self._control.start()

    def pause(self) -> RuntimeControlResult:
        return self._control.pause()

    def resume(self) -> RuntimeControlResult:
        return self._control.resume()

    def terminate(self) -> RuntimeControlResult:
        return self._control.terminate()

    def status(self) -> RuntimeControlResult:
        return self._control.status()


__all__ = ["AgentRuntimeControlService"]
