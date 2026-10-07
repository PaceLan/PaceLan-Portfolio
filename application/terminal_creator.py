"""Terminal creation control for autonomous execution."""

from dataclasses import replace

from .process_lifecycle_controller import ProcessLifecycleController
from .terminal_session import TerminalSession, TerminalSessionState
from .terminal_shell import TerminalShellResolver


class TerminalCreator:
    """Create one real terminal session."""

    def __init__(self) -> None:
        self._lifecycle = ProcessLifecycleController()
        self._resolver = TerminalShellResolver()

    def create(
        self,
        session_id: str,
        cwd: str,
        shell: str | None = None,
    ) -> TerminalSession:
        resolved = self._resolver.resolve(shell)

        session = TerminalSession(
            session_id=session_id,
            shell=resolved.executable,
            cwd=cwd,
        )

        try:
            snapshot = self._lifecycle.start(
                resolved.executable,
                resolved.argv,
                cwd=cwd,
            )
        except OSError:
            return replace(
                session,
                state=TerminalSessionState.FAILED,
            )

        return replace(
            session,
            process_id=snapshot.process_id,
            state=TerminalSessionState.RUNNING,
        )

    def snapshot(self):
        return self._lifecycle.snapshot()

    def terminate(self):
        return self._lifecycle.terminate()


__all__ = ["TerminalCreator"]
