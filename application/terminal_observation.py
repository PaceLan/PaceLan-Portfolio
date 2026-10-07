from __future__ import annotations

from typing import Any, Mapping

from application.observation_event import ObservationEvent


class TerminalObservation:
    """Normalize terminal lifecycle and output observations."""

    def created(
        self,
        *,
        terminal_id: str,
        session_id: str | None = None,
        cwd: str | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> ObservationEvent:
        return self._event(
            "CREATED",
            {
                "terminal_id": terminal_id,
                "session_id": session_id,
                "cwd": cwd,
            },
            project_id=project_id,
            task_id=task_id,
        )

    def opened(
        self,
        *,
        terminal_id: str,
        session_id: str | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> ObservationEvent:
        return self._event(
            "OPEN",
            {
                "terminal_id": terminal_id,
                "session_id": session_id,
            },
            project_id=project_id,
            task_id=task_id,
        )

    def output(
        self,
        *,
        terminal_id: str,
        output: str,
        session_id: str | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> ObservationEvent:
        return self._event(
            "OUTPUT",
            {
                "terminal_id": terminal_id,
                "session_id": session_id,
                "output": output,
            },
            project_id=project_id,
            task_id=task_id,
        )

    def exited(
        self,
        *,
        terminal_id: str,
        exit_code: int,
        session_id: str | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> ObservationEvent:
        return self._event(
            "EXITED",
            {
                "terminal_id": terminal_id,
                "session_id": session_id,
                "exit_code": exit_code,
            },
            project_id=project_id,
            task_id=task_id,
        )

    def closed(
        self,
        *,
        terminal_id: str,
        session_id: str | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> ObservationEvent:
        return self._event(
            "CLOSED",
            {
                "terminal_id": terminal_id,
                "session_id": session_id,
            },
            project_id=project_id,
            task_id=task_id,
        )

    def state(
        self,
        *,
        terminal_id: str,
        state: str,
        session_id: str | None = None,
        payload: Mapping[str, Any] | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> ObservationEvent:
        data = dict(payload or {})
        data.update(
            terminal_id=terminal_id,
            session_id=session_id,
        )
        return self._event(
            state,
            data,
            project_id=project_id,
            task_id=task_id,
        )

    @staticmethod
    def _event(
        state: str,
        payload: Mapping[str, Any],
        *,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> ObservationEvent:
        return ObservationEvent.create(
            event_type="terminal",
            source="terminal",
            observed_state=state,
            payload=payload,
            project_id=project_id,
            task_id=task_id,
        )


__all__ = ["TerminalObservation"]
