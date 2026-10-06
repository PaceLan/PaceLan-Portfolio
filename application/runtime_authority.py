from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from threading import RLock

from .runtime_control import RuntimeControlState


RuntimeAuthorityState = RuntimeControlState


class RuntimeAuthorityCommand(Enum):
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    TERMINATE = "terminate"


@dataclass(frozen=True)
class RuntimeAuthorityView:
    state: RuntimeAuthorityState
    accepted: bool
    message: str = ""


class RuntimeAuthority:
    """Single application-level authority for Agent runtime state."""

    def __init__(self) -> None:
        self._lock = RLock()
        self._state = RuntimeAuthorityState.IDLE

    def state(self) -> RuntimeAuthorityState:
        with self._lock:
            return self._state

    def view(self) -> RuntimeAuthorityView:
        with self._lock:
            return RuntimeAuthorityView(
                state=self._state,
                accepted=True,
            )

    def command(
        self,
        command: RuntimeAuthorityCommand | str,
    ) -> RuntimeAuthorityView:
        """Atomically arbitrate one runtime control command."""
        if isinstance(command, str):
            try:
                command = RuntimeAuthorityCommand(command.lower())
            except ValueError:
                with self._lock:
                    return RuntimeAuthorityView(
                        state=self._state,
                        accepted=False,
                        message=f"unsupported runtime command: {command}",
                    )

        with self._lock:
            state = self._state

            if command is RuntimeAuthorityCommand.START:
                if state is not RuntimeAuthorityState.IDLE:
                    return RuntimeAuthorityView(
                        state=state,
                        accepted=False,
                        message="start rejected: runtime is not idle",
                    )
                self._state = RuntimeAuthorityState.RUNNING

            elif command is RuntimeAuthorityCommand.PAUSE:
                if state is not RuntimeAuthorityState.RUNNING:
                    return RuntimeAuthorityView(
                        state=state,
                        accepted=False,
                        message="pause rejected: runtime is not running",
                    )
                self._state = RuntimeAuthorityState.PAUSED

            elif command is RuntimeAuthorityCommand.RESUME:
                if state is not RuntimeAuthorityState.PAUSED:
                    return RuntimeAuthorityView(
                        state=state,
                        accepted=False,
                        message="resume rejected: runtime is not paused",
                    )
                self._state = RuntimeAuthorityState.RUNNING

            elif command in {
                RuntimeAuthorityCommand.STOP,
                RuntimeAuthorityCommand.TERMINATE,
            }:
                if state not in {
                    RuntimeAuthorityState.RUNNING,
                    RuntimeAuthorityState.PAUSED,
                }:
                    return RuntimeAuthorityView(
                        state=state,
                        accepted=False,
                        message="stop rejected: runtime is not active",
                    )
                self._state = RuntimeAuthorityState.TERMINATED

            return RuntimeAuthorityView(
                state=self._state,
                accepted=True,
                message=f"{command.value} accepted",
            )

    def _require_command(
        self,
        command: RuntimeAuthorityCommand,
    ) -> RuntimeAuthorityView:
        result = self.command(command)
        if not result.accepted:
            raise RuntimeError(result.message)
        return result

    def start(self) -> RuntimeAuthorityView:
        return self._require_command(RuntimeAuthorityCommand.START)

    def pause(self) -> RuntimeAuthorityView:
        return self._require_command(RuntimeAuthorityCommand.PAUSE)

    def resume(self) -> RuntimeAuthorityView:
        return self._require_command(RuntimeAuthorityCommand.RESUME)

    def terminate(self) -> RuntimeAuthorityView:
        return self._require_command(RuntimeAuthorityCommand.TERMINATE)

    def reset(self) -> RuntimeAuthorityView:
        with self._lock:
            self._state = RuntimeAuthorityState.IDLE
            return self.view()


__all__ = [
    "RuntimeAuthority",
    "RuntimeAuthorityCommand",
    "RuntimeAuthorityState",
    "RuntimeAuthorityView",
]
