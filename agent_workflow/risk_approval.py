"""Risk and approval awareness for deterministic workflow execution."""

from dataclasses import dataclass
from enum import Enum

from agent_workflow.workflow_plan import WorkflowStep
from permissions.reporting import ApprovalStatus, RiskLevel


class ExecutionReadiness(str, Enum):
    """Deterministic readiness states for one workflow step."""

    READY = "READY"
    BLOCKED = "BLOCKED"


@dataclass(frozen=True)
class RiskApprovalAssessment:
    """Immutable safety assessment for one workflow step."""

    step_id: str
    risk: RiskLevel
    approval: ApprovalStatus
    readiness: ExecutionReadiness
    reason: str

    @property
    def is_ready(self) -> bool:
        return self.readiness is ExecutionReadiness.READY


class RiskApprovalAwareness:
    """Evaluate workflow-step risk and approval without executing actions."""

    @staticmethod
    def assess(step: WorkflowStep) -> RiskApprovalAssessment:
        if step.approval in {
            ApprovalStatus.DENIED,
            ApprovalStatus.BLOCKED,
        }:
            return RiskApprovalAssessment(
                step_id=step.step_id,
                risk=step.risk,
                approval=step.approval,
                readiness=ExecutionReadiness.BLOCKED,
                reason="approval status blocks execution",
            )

        if (
            step.risk is RiskLevel.HIGH_RISK
            and step.approval is not ApprovalStatus.APPROVED
        ):
            return RiskApprovalAssessment(
                step_id=step.step_id,
                risk=step.risk,
                approval=step.approval,
                readiness=ExecutionReadiness.BLOCKED,
                reason="high-risk step requires approval",
            )

        return RiskApprovalAssessment(
            step_id=step.step_id,
            risk=step.risk,
            approval=step.approval,
            readiness=ExecutionReadiness.READY,
            reason="risk and approval requirements satisfied",
        )

    @classmethod
    def assess_plan(
        cls,
        steps: tuple[WorkflowStep, ...],
    ) -> tuple[RiskApprovalAssessment, ...]:
        return tuple(cls.assess(step) for step in steps)

    @classmethod
    def is_plan_ready(
        cls,
        steps: tuple[WorkflowStep, ...],
    ) -> bool:
        return all(
            assessment.is_ready
            for assessment in cls.assess_plan(steps)
        )


class ExecutionReadinessGate:
    """Deterministic execution gate based on risk and approval assessment."""

    @classmethod
    def assess(cls, step: WorkflowStep) -> RiskApprovalAssessment:
        """Assess one step without executing its action."""
        return RiskApprovalAwareness.assess(step)

    @classmethod
    def can_execute(cls, step: WorkflowStep) -> bool:
        """Return whether a step is safe to enter execution."""
        return cls.assess(step).is_ready

    @classmethod
    def assess_plan(
        cls,
        steps: tuple[WorkflowStep, ...],
    ) -> tuple[RiskApprovalAssessment, ...]:
        """Assess all steps without executing any action."""
        return RiskApprovalAwareness.assess_plan(steps)

    @classmethod
    def is_plan_ready(
        cls,
        steps: tuple[WorkflowStep, ...],
    ) -> bool:
        """Return whether every step passes the execution gate."""
        return all(
            assessment.is_ready
            for assessment in cls.assess_plan(steps)
        )
