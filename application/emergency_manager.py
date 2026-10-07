from __future__ import annotations

from dataclasses import dataclass

from application.emergency_classification import (
    EmergencyClassification,
    EmergencyClassifier,
)
from application.emergency_detector import (
    EmergencyDetection,
    EmergencyDetector,
)
from application.emergency_snapshot import EmergencySnapshot
from application.observation_event import ObservationEvent


@dataclass(frozen=True)
class EmergencyManagementResult:
    """Current emergency lifecycle result without recovery side effects."""

    detection: EmergencyDetection
    classification: EmergencyClassification | None
    snapshot: EmergencySnapshot | None
    recovery_started: bool = False
    verification_started: bool = False
    escalation_started: bool = False


class EmergencyManager:
    """Orchestrate emergency detection, classification, and snapshot creation."""

    def __init__(
        self,
        detector: EmergencyDetector | None = None,
        classifier: EmergencyClassifier | None = None,
    ) -> None:
        self._detector = detector or EmergencyDetector()
        self._classifier = classifier or EmergencyClassifier()

    def process(self, event: ObservationEvent) -> EmergencyManagementResult:
        if not isinstance(event, ObservationEvent):
            raise TypeError("event must be an ObservationEvent")

        detection = self._detector.detect(event)

        if not detection.detected:
            return EmergencyManagementResult(
                detection=detection,
                classification=None,
                snapshot=None,
            )

        classification = self._classifier.classify(detection)
        snapshot = EmergencySnapshot.create(classification)

        return EmergencyManagementResult(
            detection=detection,
            classification=classification,
            snapshot=snapshot,
        )


__all__ = ["EmergencyManagementResult", "EmergencyManager"]
