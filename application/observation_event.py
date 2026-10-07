from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Mapping
from uuid import uuid4


@dataclass(frozen=True)
class ObservationEvent:
    event_id: str
    event_type: str
    source: str
    timestamp: str
    observed_state: str
    payload: Mapping[str, Any] = field(default_factory=dict)
    project_id: str | None = None
    task_id: str | None = None
    workflow_id: str | None = None
    execution_id: str | None = None
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        for name in ("event_id", "event_type", "source", "timestamp", "observed_state"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must not be empty")

        try:
            datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise ValueError("timestamp must be a valid ISO-8601 timestamp") from exc

        if not isinstance(self.payload, Mapping):
            raise TypeError("payload must be a mapping")

    @classmethod
    def create(
        cls,
        *,
        event_type: str,
        source: str,
        observed_state: str,
        payload: Mapping[str, Any] | None = None,
        project_id: str | None = None,
        task_id: str | None = None,
        workflow_id: str | None = None,
        execution_id: str | None = None,
        correlation_id: str | None = None,
        event_id: str | None = None,
        timestamp: str | None = None,
    ) -> "ObservationEvent":
        return cls(
            event_id=event_id or str(uuid4()),
            event_type=event_type,
            source=source,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
            observed_state=observed_state,
            payload=dict(payload or {}),
            project_id=project_id,
            task_id=task_id,
            workflow_id=workflow_id,
            execution_id=execution_id,
            correlation_id=correlation_id,
        )


__all__ = ["ObservationEvent"]
