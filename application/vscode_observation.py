from __future__ import annotations

from typing import Any, Mapping

from application.observation_event import ObservationEvent


class VSCodeObservation:
    """Normalize VS Code observations into ObservationEvent."""

    def workspace(self, *, root: str | None, state: str, project_id: str | None = None) -> ObservationEvent:
        return self._create("workspace", state, {"root": root}, project_id=project_id)

    def problem(
        self,
        *,
        severity: str,
        message: str,
        resource: str | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> ObservationEvent:
        return self._create(
            "problem",
            severity,
            {"severity": severity, "message": message, "resource": resource},
            project_id=project_id,
            task_id=task_id,
        )

    def error(
        self,
        *,
        message: str,
        source: str | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
    ) -> ObservationEvent:
        return self._create(
            "error",
            "error",
            {"message": message, "source": source},
            project_id=project_id,
            task_id=task_id,
        )

    def extension(
        self,
        *,
        extension_id: str,
        state: str,
        project_id: str | None = None,
    ) -> ObservationEvent:
        return self._create(
            "extension",
            state,
            {"extension_id": extension_id},
            project_id=project_id,
        )

    def connection(
        self,
        *,
        state: str,
        payload: Mapping[str, Any] | None = None,
    ) -> ObservationEvent:
        return self._create("connection", state, dict(payload or {}))

    def command(
        self,
        *,
        command: str,
        state: str,
        payload: Mapping[str, Any] | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
        workflow_id: str | None = None,
        execution_id: str | None = None,
    ) -> ObservationEvent:
        data = dict(payload or {})
        data["command"] = command
        return self._create(
            "command",
            state,
            data,
            project_id=project_id,
            task_id=task_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
        )

    @staticmethod
    def _create(
        event_type: str,
        state: str,
        payload: Mapping[str, Any],
        *,
        project_id: str | None = None,
        task_id: str | None = None,
        workflow_id: str | None = None,
        execution_id: str | None = None,
    ) -> ObservationEvent:
        return ObservationEvent.create(
            event_type=event_type,
            source="vscode",
            observed_state=state,
            payload=payload,
            project_id=project_id,
            task_id=task_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
        )


__all__ = ["VSCodeObservation"]
