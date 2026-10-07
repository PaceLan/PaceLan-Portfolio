from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from application.emergency_classification import EmergencyClassification


class RecoveryDecision(str, Enum):
    IMMEDIATE_RECOVERY = "IMMEDIATE_RECOVERY"
    WAITING_EXTERNAL = "WAITING_EXTERNAL"
    WAITING_FOR_USER = "WAITING_FOR_USER"
    STOP = "STOP"


@dataclass(frozen=True)
class RecoveryDecisionResult:
    decision: RecoveryDecision
    classification: EmergencyClassification


class RecoveryDecisionEngine:
    """Select the next recovery state without executing recovery."""

    def decide(
        self,
        classification: EmergencyClassification,
    ) -> RecoveryDecisionResult:
        if not isinstance(classification, EmergencyClassification):
            raise TypeError("classification must be an EmergencyClassification")

        event = classification.detection.event
        payload = dict(event.payload) if event is not None else {}
        reason = str(payload.get("reason", "")).strip().lower()

        if classification.recoverability == "recovery_candidate":
            decision = RecoveryDecision.IMMEDIATE_RECOVERY
        elif classification.recoverability == "waiting_external":
            if reason == "safety_check":
                decision = RecoveryDecision.WAITING_FOR_USER
            elif reason in {"connection_lost", "quota_limit"}:
                decision = RecoveryDecision.WAITING_EXTERNAL
            else:
                decision = RecoveryDecision.STOP
        else:
            decision = RecoveryDecision.STOP

        return RecoveryDecisionResult(
            decision=decision,
            classification=classification,
        )


__all__ = [
    "RecoveryDecision",
    "RecoveryDecisionResult",
    "RecoveryDecisionEngine",
]
