from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from application.observation_event import ObservationEvent


@dataclass(frozen=True)
class ObservationCorrelation:
    """Stable correlation view for one observation event."""

    event: ObservationEvent
    correlation_key: str
    basis: str


class ObservationCorrelator:
    """Correlate observation events using existing stable identifiers only."""

    _BASES = (
        ("correlation_id", "correlation"),
        ("execution_id", "execution"),
        ("workflow_id", "workflow"),
        ("task_id", "task"),
        ("project_id", "project"),
    )

    def correlate(self, event: ObservationEvent) -> ObservationCorrelation:
        if not isinstance(event, ObservationEvent):
            raise TypeError("event must be an ObservationEvent")

        for field_name, basis in self._BASES:
            value = getattr(event, field_name)
            if isinstance(value, str) and value.strip():
                return ObservationCorrelation(
                    event=event,
                    correlation_key=value.strip(),
                    basis=basis,
                )

        return ObservationCorrelation(
            event=event,
            correlation_key=event.event_id,
            basis="event",
        )

    def group(
        self,
        events: Iterable[ObservationEvent],
    ) -> dict[str, tuple[ObservationCorrelation, ...]]:
        groups: dict[str, list[ObservationCorrelation]] = {}

        for event in events:
            correlation = self.correlate(event)
            groups.setdefault(correlation.correlation_key, []).append(correlation)

        return {
            key: tuple(values)
            for key, values in groups.items()
        }


__all__ = ["ObservationCorrelation", "ObservationCorrelator"]
