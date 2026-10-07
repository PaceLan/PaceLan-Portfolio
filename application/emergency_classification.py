from __future__ import annotations

from dataclasses import dataclass

from application.emergency_detector import EmergencyDetection


@dataclass(frozen=True)
class EmergencyClassification:
    """Classification of one detected emergency."""
    category: str
    severity: str
    recoverability: str
    impact: str
    detection: EmergencyDetection


class EmergencyClassifier:
    """Classify detected emergencies without executing recovery."""

    _CLASSIFICATIONS = {
        "process_crashed": ("process", "critical", "recovery_candidate", "execution"),
        "process_hung": ("process", "high", "recovery_candidate", "execution"),
        "process_failed": ("process", "high", "recovery_candidate", "execution"),
        "terminal_failed": ("terminal", "high", "recovery_candidate", "execution"),
        "terminal_disconnected": ("terminal", "high", "recovery_candidate", "execution"),
        "external_agent_failed": (
            "external_agent",
            "high",
            "recovery_candidate",
            "external_dependency",
        ),
        "external_agent_waiting": (
            "external_agent",
            "medium",
            "waiting_external",
            "external_dependency",
        ),
        "execution_failed": (
            "execution",
            "high",
            "recovery_candidate",
            "execution",
        ),
        "vscode_error": (
            "vscode",
            "high",
            "recovery_candidate",
            "development_environment",
        ),
    }

    def classify(self, detection: EmergencyDetection) -> EmergencyClassification:
        if not isinstance(detection, EmergencyDetection):
            raise TypeError("detection must be an EmergencyDetection")

        if not detection.detected:
            raise ValueError("only detected emergencies can be classified")

        if not detection.reason:
            raise ValueError("detected emergency requires a reason")

        classification = self._CLASSIFICATIONS.get(detection.reason)
        if classification is None:
            raise ValueError(
                f"unknown emergency reason: {detection.reason}"
            )

        category, severity, recoverability, impact = classification

        return EmergencyClassification(
            category=category,
            severity=severity,
            recoverability=recoverability,
            impact=impact,
            detection=detection,
        )


__all__ = ["EmergencyClassification", "EmergencyClassifier"]
