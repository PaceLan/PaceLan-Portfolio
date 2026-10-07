from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from application.emergency_manager import EmergencyManager
from application.observation_event import ObservationEvent
from application.recovery_decision import (
    RecoveryDecision,
    RecoveryDecisionEngine,
    RecoveryDecisionResult,
)
from application.recovery_escalation import (
    RecoveryEscalationResult,
    RecoveryEscalationService,
)
from application.recovery_execution import (
    RecoveryExecutionResult,
    RecoveryExecutionService,
)
from application.recovery_state_storage import (
    RecoveryState,
    RecoveryStateStorage,
)
from application.recovery_verification import (
    RecoveryVerificationResult,
    RecoveryVerificationService,
)
from application.user_intervention_boundary import (
    UserInterventionBoundary,
    UserInterventionResult,
)


@dataclass(frozen=True)
class EmergencyRecoveryResult:
    recovery_id: str
    emergency: bool
    decision: RecoveryDecisionResult | None
    execution: RecoveryExecutionResult | None
    verification: RecoveryVerificationResult | None
    escalation: RecoveryEscalationResult | None
    intervention: UserInterventionResult | None
    status: str
    message: str = ""


class EmergencyRecoveryOrchestrator:
    """Coordinate the complete emergency recovery lifecycle."""

    def __init__(
        self,
        *,
        emergency_manager: EmergencyManager | None = None,
        decision_engine: RecoveryDecisionEngine | None = None,
        execution_service: RecoveryExecutionService | None = None,
        verification_service: RecoveryVerificationService | None = None,
        escalation_service: RecoveryEscalationService | None = None,
        intervention_boundary: UserInterventionBoundary | None = None,
        state_storage: RecoveryStateStorage | None = None,
    ) -> None:
        self._manager = emergency_manager or EmergencyManager()
        self._decision = decision_engine or RecoveryDecisionEngine()
        self._execution = execution_service or RecoveryExecutionService()
        self._verification = verification_service or RecoveryVerificationService()
        self._escalation = escalation_service or RecoveryEscalationService()
        self._intervention = (
            intervention_boundary or UserInterventionBoundary()
        )
        self._storage = state_storage

    def recover(
        self,
        event: ObservationEvent,
        *,
        expected_state: str,
        attempt: int = 0,
    ) -> EmergencyRecoveryResult:
        if not isinstance(event, ObservationEvent):
            raise TypeError("event must be an ObservationEvent")
        if not isinstance(expected_state, str) or not expected_state.strip():
            raise ValueError("expected_state must be a non-empty string")
        if not isinstance(attempt, int) or isinstance(attempt, bool):
            raise TypeError("attempt must be an integer")
        if attempt < 0:
            raise ValueError("attempt must not be negative")

        emergency = self._manager.process(event)
        if not emergency.detection.detected:
            return EmergencyRecoveryResult(
                recovery_id="",
                emergency=False,
                decision=None,
                execution=None,
                verification=None,
                escalation=None,
                intervention=None,
                status="NO_EMERGENCY",
                message="observation event is not an emergency",
            )

        if emergency.classification is None or emergency.snapshot is None:
            raise RuntimeError("emergency result is missing recovery context")

        recovery_id = str(uuid4())
        self._persist(
            recovery_id,
            emergency.snapshot.snapshot_id,
            "DETECTED",
            emergency.detection.reason or "",
            0,
        )

        decision = self._decision.decide(emergency.classification)
        self._persist(
            recovery_id,
            emergency.snapshot.snapshot_id,
            decision.decision.value,
            emergency.detection.reason or "",
            1,
        )

        execution = self._execution.execute(decision.decision)

        if execution.outcome in {
            execution.outcome.WAITING_EXTERNAL,
            execution.outcome.WAITING_FOR_USER,
        }:
            verification = self._verification.verify(
                execution,
                expected_state=expected_state,
            )
            escalation = self._escalation.decide(
                verification,
                attempt=attempt,
            )
            intervention = self._intervention.decide(
                execution,
                escalation,
            )
            status = execution.outcome.value
            self._persist(
                recovery_id,
                emergency.snapshot.snapshot_id,
                status,
                execution.message,
                2,
            )
            return EmergencyRecoveryResult(
                recovery_id=recovery_id,
                emergency=True,
                decision=decision,
                execution=execution,
                verification=verification,
                escalation=escalation,
                intervention=intervention,
                status=status,
                message=execution.message,
            )

        verification = self._verification.verify(
            execution,
            expected_state=expected_state,
        )
        escalation = self._escalation.decide(
            verification,
            attempt=attempt,
        )
        intervention = self._intervention.decide(
            execution,
            escalation,
        )

        if verification.verified:
            status = "VERIFIED"
        elif escalation.outcome.value == "ESCALATE":
            status = "ESCALATE"
        elif escalation.outcome.value == "STOP":
            status = "STOP"
        else:
            status = verification.status.value

        self._persist(
            recovery_id,
            emergency.snapshot.snapshot_id,
            status,
            verification.message,
            2,
        )

        return EmergencyRecoveryResult(
            recovery_id=recovery_id,
            emergency=True,
            decision=decision,
            execution=execution,
            verification=verification,
            escalation=escalation,
            intervention=intervention,
            status=status,
            message=verification.message,
        )

    def _persist(
        self,
        recovery_id: str,
        snapshot_id: str,
        status: str,
        reason: str,
        sequence: int,
    ) -> None:
        if self._storage is None:
            return

        self._storage.save(
            RecoveryState(
                recovery_id=recovery_id,
                snapshot_id=snapshot_id,
                status=status,
                reason=reason,
                sequence=sequence,
            )
        )


__all__ = [
    "EmergencyRecoveryOrchestrator",
    "EmergencyRecoveryResult",
]
