from __future__ import annotations

from typing import Any, Mapping

from application.observation_event import ObservationEvent


class EventNormalizer:
    """Normalize ObservationEvent instances without changing their meaning."""

    def normalize(self, event: ObservationEvent) -> ObservationEvent:
        if not isinstance(event, ObservationEvent):
            raise TypeError("event must be an ObservationEvent")

        source = self._normalize_token(event.source)
        event_type = self._normalize_event_type(source, event.event_type)
        state = self._normalize_state(event.observed_state)

        payload = dict(event.payload)
        payload["normalized_source"] = source
        payload["normalized_event_type"] = event_type
        payload["normalized_state"] = state

        return ObservationEvent.create(
            event_type=event_type,
            source=source,
            observed_state=state,
            payload=payload,
            project_id=event.project_id,
            task_id=event.task_id,
            workflow_id=event.workflow_id,
            execution_id=event.execution_id,
            correlation_id=event.correlation_id,
            event_id=event.event_id,
            timestamp=event.timestamp,
        )

    @staticmethod
    def _normalize_token(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("event source must not be empty")
        return value.strip().lower()

    @classmethod
    def _normalize_event_type(cls, source: str, event_type: str) -> str:
        normalized = cls._normalize_token(event_type)
        prefix = f"{source}."
        if normalized.startswith(prefix):
            return normalized
        return f"{prefix}{normalized}"

    @staticmethod
    def _normalize_state(value: str) -> str:
        if not isinstance(value, str) or not value.strip():
            raise ValueError("event state must not be empty")
        return value.strip().lower()


__all__ = ["EventNormalizer"]
