from __future__ import annotations

from dataclasses import dataclass
from application.observation_event import ObservationEvent


@dataclass(frozen=True)
class EmergencyDetection:
    """Detection result for one observation event."""
    detected: bool
    reason: str | None = None
    event: ObservationEvent | None = None


class EmergencyDetector:
    """Detect real emergency-triggering observation states."""

    _TRIGGERS = {
        ("process", "CRASHED"): "process_crashed",
        ("process", "HUNG"): "process_hung",
        ("process", "FAILED"): "process_failed",
        ("terminal", "FAILED"): "terminal_failed",
        ("terminal", "DISCONNECTED"): "terminal_disconnected",
        ("external_agent", "FAILED"): "external_agent_failed",
        ("external_agent", "WAITING_EXTERNAL"): "external_agent_waiting",
        ("execution", "FAILED"): "execution_failed",
        ("vscode", "error"): "vscode_error",
    }

    def detect(self, event: ObservationEvent) -> EmergencyDetection:
        if not isinstance(event, ObservationEvent):
            raise TypeError("event must be an ObservationEvent")

        key = (
            event.source.strip().lower(),
            event.observed_state.strip().upper(),
        )

        reason = self._TRIGGERS.get(key)
        if reason is None:
            normalized_type = event.event_type.strip().lower()
            if (
                event.source.strip().lower() == "vscode"
                and normalized_type == "error"
            ):
                reason = "vscode_error"

        return EmergencyDetection(
            detected=reason is not None,
            reason=reason,
            event=event if reason is not None else None,
        )


__all__ = ["EmergencyDetection", "EmergencyDetector"]
