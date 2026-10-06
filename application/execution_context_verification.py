"""Verification of restored execution contexts."""
from dataclasses import dataclass

from application.execution_context_restore import (
    RestoredExecutionContext,
)


@dataclass(frozen=True)
class ExecutionContextVerification:
    valid: bool
    requires_process_revalidation: bool
    requires_terminal_revalidation: bool
    reason: str


def verify_execution_context(
    restored: RestoredExecutionContext,
) -> ExecutionContextVerification:
    if not isinstance(
        restored,
        RestoredExecutionContext,
    ):
        raise TypeError(
            "restored must be a RestoredExecutionContext"
        )

    context = restored.context

    if not context.project_id.strip():
        return ExecutionContextVerification(
            False,
            restored.process_revalidation_required,
            restored.terminal_revalidation_required,
            "project identity is missing",
        )

    if not context.task_id.strip():
        return ExecutionContextVerification(
            False,
            restored.process_revalidation_required,
            restored.terminal_revalidation_required,
            "task identity is missing",
        )

    if not context.run_id.strip():
        return ExecutionContextVerification(
            False,
            restored.process_revalidation_required,
            restored.terminal_revalidation_required,
            "run identity is missing",
        )

    if not context.step_id.strip():
        return ExecutionContextVerification(
            False,
            restored.process_revalidation_required,
            restored.terminal_revalidation_required,
            "step identity is missing",
        )

    if context.checkpoint_sequence < 0:
        return ExecutionContextVerification(
            False,
            restored.process_revalidation_required,
            restored.terminal_revalidation_required,
            "checkpoint sequence is invalid",
        )

    return ExecutionContextVerification(
        True,
        restored.process_revalidation_required,
        restored.terminal_revalidation_required,
        "execution context is structurally valid",
    )
