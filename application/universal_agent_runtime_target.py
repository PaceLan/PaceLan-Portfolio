from __future__ import annotations

from application.runtime_control import RuntimeControlState
from application.universal_agent_interface import UniversalAgentInterface


class UniversalAgentRuntimeTarget:
    """Adapts one UniversalAgent task to application runtime controls."""

    def __init__(
        self,
        agent: UniversalAgentInterface,
        task_id: str,
    ) -> None:
        if not isinstance(task_id, str) or not task_id.strip():
            raise ValueError("task_id must be a non-empty string")

        self._agent = agent
        self._task_id = task_id

    def start_runtime(self) -> None:
        self._agent.start(self._task_id)

    def pause_runtime(self) -> None:
        self._agent.pause(self._task_id)

    def resume_runtime(self) -> None:
        self._agent.resume(self._task_id)

    def terminate_runtime(self) -> None:
        self._agent.stop(self._task_id)

    def runtime_state(self) -> str:
        runtime = self._agent.inspect_runtime()
        mapping = {
            "IDLE": RuntimeControlState.IDLE.value,
            "RUNNING": RuntimeControlState.RUNNING.value,
            "PAUSED": RuntimeControlState.PAUSED.value,
            "STOPPED": RuntimeControlState.TERMINATED.value,
        }
        return mapping.get(
            runtime.state.value,
            RuntimeControlState.TERMINATED.value,
        )


__all__ = ["UniversalAgentRuntimeTarget"]
