from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from application.recovery_escalation import (
    RecoveryEscalation,
    RecoveryEscalationResult,
)
from application.recovery_execution import (
    RecoveryExecution,
    RecoveryExecutionResult,
)


class UserInterventionRequirement(str, Enum):
    REQUIRED = "REQUIRED"
    NOT_REQUIRED = "NOT_REQUIRED"


@dataclass(frozen=True)
class UserInterventionResult:
    requirement: UserInterventionRequirement
    reason: str


class UserInterventionBoundary:
    """Determine whether recovery requires explicit user intervention."""

    def decide(
        self,
        execution: RecoveryExecutionResult,
        escalation: RecoveryEscalationResult,
    ) -> UserInterventionResult:
        if not isinstance(execution, RecoveryExecutionResult):
            raise TypeError("execution must be a RecoveryExecutionResult")
        if not isinstance(escalation, RecoveryEscalationResult):
            raise TypeError("escalation must be a RecoveryEscalationResult")

        if execution.outcome is RecoveryExecution.WAITING_FOR_USER:
            return UserInterventionResult(
                UserInterventionRequirement.REQUIRED,
                "recovery is waiting for user intervention",
            )

        if execution.outcome is RecoveryExecution.STOP:
            return UserInterventionResult(
                UserInterventionRequirement.REQUIRED,
                "recovery execution stopped",
            )

        if execution.outcome is RecoveryExecution.FAILED:
            return UserInterventionResult(
                UserInterventionRequirement.REQUIRED,
                "recovery execution failed",
            )

        if escalation.outcome is RecoveryEscalation.ESCALATE:
            return UserInterventionResult(
                UserInterventionRequirement.REQUIRED,
                "recovery escalation requires user intervention",
            )

        if escalation.outcome is RecoveryEscalation.STOP:
            return UserInterventionResult(
                UserInterventionRequirement.REQUIRED,
                "recovery escalation stopped",
            )

        if execution.outcome is RecoveryExecution.WAITING_EXTERNAL:
            return UserInterventionResult(
                UserInterventionRequirement.NOT_REQUIRED,
                "recovery is waiting for an external dependency",
            )

        if escalation.outcome is RecoveryEscalation.WAITING:
            return UserInterventionResult(
                UserInterventionRequirement.NOT_REQUIRED,
                "recovery is waiting",
            )

        return UserInterventionResult(
            UserInterventionRequirement.NOT_REQUIRED,
            "user intervention is not required",
        )


__all__ = [
    "UserInterventionRequirement",
    "UserInterventionResult",
    "UserInterventionBoundary",
]
