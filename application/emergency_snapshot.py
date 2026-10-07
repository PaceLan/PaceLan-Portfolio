from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from application.emergency_classification import EmergencyClassification
from application.observation_event import ObservationEvent


@dataclass(frozen=True)
class EmergencySnapshot:
    """Immutable point-in-time snapshot of a detected emergency."""

    snapshot_id: str
    captured_at: datetime
    category: str
    severity: str
    recoverability: str
    impact: str
    event: ObservationEvent
    project_id: str | None
    task_id: str | None
    workflow_id: str | None
    execution_id: str | None

    @classmethod
    def create(
        cls,
        classification: EmergencyClassification,
    ) -> "EmergencySnapshot":
        if not isinstance(classification, EmergencyClassification):
            raise TypeError(
                "classification must be an EmergencyClassification"
            )

        event = classification.detection.event
        if not isinstance(event, ObservationEvent):
            raise ValueError(
                "emergency classification must contain its observation event"
            )

        from uuid import uuid4

        return cls(
            snapshot_id=str(uuid4()),
            captured_at=datetime.now(timezone.utc),
            category=classification.category,
            severity=classification.severity,
            recoverability=classification.recoverability,
            impact=classification.impact,
            event=ObservationEvent.create(
                event_type=event.event_type,
                source=event.source,
                timestamp=event.timestamp,
                observed_state=event.observed_state,
                payload=dict(event.payload),
                project_id=event.project_id,
                task_id=event.task_id,
                workflow_id=event.workflow_id,
                execution_id=event.execution_id,
                correlation_id=event.correlation_id,
                event_id=event.event_id,
            ),
            project_id=event.project_id,
            task_id=event.task_id,
            workflow_id=event.workflow_id,
            execution_id=event.execution_id,
        )


__all__ = ["EmergencySnapshot"]
