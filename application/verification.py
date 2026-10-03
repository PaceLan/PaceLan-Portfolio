from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from agent_workflow.workflow_result import WorkflowResult


class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    NOT_VERIFIED = "not_verified"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class VerificationResult:
    run_id: str
    status: VerificationStatus
    verified: bool
    reason: str
    checked_steps: int
    successful_steps: int
    failed_steps: int
    blocked_steps: int


class VerificationService:
    """Application-level verification of an already completed workflow result."""

    @staticmethod
    def verify(result: WorkflowResult) -> VerificationResult:
        if not isinstance(result, WorkflowResult):
            raise TypeError("result must be a WorkflowResult")

        if result.blocked_steps:
            return VerificationResult(
                run_id=result.run_id,
                status=VerificationStatus.BLOCKED,
                verified=False,
                reason="Workflow contains blocked steps.",
                checked_steps=result.total_steps,
                successful_steps=result.successful_steps,
                failed_steps=result.failed_steps,
                blocked_steps=result.blocked_steps,
            )

        if result.failed_steps or not result.completed_successfully:
            return VerificationResult(
                run_id=result.run_id,
                status=VerificationStatus.NOT_VERIFIED,
                verified=False,
                reason="Workflow did not complete successfully.",
                checked_steps=result.total_steps,
                successful_steps=result.successful_steps,
                failed_steps=result.failed_steps,
                blocked_steps=result.blocked_steps,
            )

        return VerificationResult(
            run_id=result.run_id,
            status=VerificationStatus.VERIFIED,
            verified=True,
            reason="Workflow completed successfully.",
            checked_steps=result.total_steps,
            successful_steps=result.successful_steps,
            failed_steps=result.failed_steps,
            blocked_steps=result.blocked_steps,
        )


__all__ = [
    "VerificationResult",
    "VerificationService",
    "VerificationStatus",
]
