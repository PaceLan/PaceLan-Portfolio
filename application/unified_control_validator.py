from __future__ import annotations

from application.models import (
    ApplicationExecutionModel,
    TaskModel,
)
from application.runtime_authority import RuntimeAuthority
from application.runtime_control import RuntimeControlState
from application.verification import VerificationStatus


class UnifiedControlValidator:
    """Validate the complete application execution state chain."""

    @staticmethod
    def validate(
        execution: ApplicationExecutionModel,
        runtime_authority: RuntimeAuthority,
    ) -> None:
        if not isinstance(execution, ApplicationExecutionModel):
            raise TypeError("execution must be an ApplicationExecutionModel")
        if not isinstance(runtime_authority, RuntimeAuthority):
            raise TypeError("runtime_authority must be a RuntimeAuthority")

        if not isinstance(execution.task, TaskModel):
            raise TypeError("execution.task must be a TaskModel")

        if execution.task.task_id != execution.plan.task_id:
            raise ValueError("task_id must match between task and plan")

        if execution.task.project_id != execution.plan.project_id:
            raise ValueError("project_id must match between task and plan")

        if execution.task.task_id != execution.run.task_id:
            raise ValueError("task_id must match between task and run")

        if execution.run.run_id != execution.result.run_id:
            raise ValueError("run_id must match between run and result")

        if execution.run.run_id != execution.snapshot.run_id:
            raise ValueError("run_id must match between run and snapshot")

        if execution.task.task_id != execution.snapshot.task_id:
            raise ValueError("task_id must match between task and snapshot")

        verification = execution.verification
        if verification is None:
            raise ValueError("verification is required")

        if verification.run_id != execution.run.run_id:
            raise ValueError("run_id must match between run and verification")

        runtime_state = runtime_authority.state()

        terminal_result = execution.result.status in {
            "COMPLETED",
            "FAILED",
            "BLOCKED",
        }

        if terminal_result and runtime_state not in {
            RuntimeControlState.IDLE,
            RuntimeControlState.TERMINATED,
        }:
            raise ValueError(
                "terminal result requires a non-active runtime state"
            )

        expected_verification = {
            "COMPLETED": VerificationStatus.VERIFIED,
            "FAILED": VerificationStatus.NOT_VERIFIED,
            "BLOCKED": VerificationStatus.BLOCKED,
        }.get(execution.result.status)

        if (
            expected_verification is not None
            and verification.status is not expected_verification
        ):
            raise ValueError(
                "verification status does not match execution result"
            )


__all__ = ["UnifiedControlValidator"]
