from __future__ import annotations

from application.models import ResultModel, RunModel
from application.verification import VerificationResult, VerificationStatus


class ExecutionVerificationValidator:
    """Validate consistency between execution result and verification."""

    @staticmethod
    def validate(
        run: RunModel,
        result: ResultModel,
        verification: VerificationResult,
    ) -> None:
        if not isinstance(run, RunModel):
            raise TypeError("run must be a RunModel")
        if not isinstance(result, ResultModel):
            raise TypeError("result must be a ResultModel")
        if not isinstance(verification, VerificationResult):
            raise TypeError("verification must be a VerificationResult")

        if run.run_id != result.run_id or run.run_id != verification.run_id:
            raise ValueError("run_id must match across execution and verification")

        if verification.checked_steps != result.total_steps:
            raise ValueError("verification step count must match result")

        if verification.successful_steps != result.successful_steps:
            raise ValueError("verification successful step count must match result")

        if verification.failed_steps != result.failed_steps:
            raise ValueError("verification failed step count must match result")

        if verification.blocked_steps != result.blocked_steps:
            raise ValueError("verification blocked step count must match result")

        expected = {
            "COMPLETED": VerificationStatus.VERIFIED,
            "FAILED": VerificationStatus.NOT_VERIFIED,
            "BLOCKED": VerificationStatus.BLOCKED,
        }.get(result.status)

        if expected is not None and verification.status is not expected:
            raise ValueError("verification status does not match result")


__all__ = ["ExecutionVerificationValidator"]
