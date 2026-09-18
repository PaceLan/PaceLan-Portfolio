"""Analysis of immutable workflow results without executing workflows."""

from dataclasses import dataclass
from typing import Tuple

from agent_workflow.workflow_core import WorkflowStatus, WorkflowStepResult
from agent_workflow.workflow_result import WorkflowResult


@dataclass(frozen=True)
class WorkflowResultAnalysis:
    """Immutable analysis derived from one WorkflowResult."""

    is_successful: bool
    has_failure: bool
    has_blocked_step: bool
    first_failed_step: WorkflowStepResult | None
    failed_operations: Tuple[str, ...]
    blocked_operations: Tuple[str, ...]
    successful_operations: Tuple[str, ...]

    @classmethod
    def from_result(
        cls,
        result: WorkflowResult,
    ) -> "WorkflowResultAnalysis":
        """Build deterministic analysis from an existing WorkflowResult."""
        if not isinstance(result, WorkflowResult):
            raise TypeError("result must be a WorkflowResult instance")

        failed_steps = tuple(
            step
            for step in result.step_results
            if step.status is WorkflowStatus.FAILED
        )

        blocked_steps = tuple(
            step
            for step in result.step_results
            if step.status is WorkflowStatus.BLOCKED
        )

        successful_steps = tuple(
            step
            for step in result.step_results
            if step.success
        )

        return cls(
            is_successful=result.completed_successfully,
            has_failure=bool(failed_steps),
            has_blocked_step=bool(blocked_steps),
            first_failed_step=failed_steps[0] if failed_steps else None,
            failed_operations=tuple(
                step.operation for step in failed_steps
            ),
            blocked_operations=tuple(
                step.operation for step in blocked_steps
            ),
            successful_operations=tuple(
                step.operation for step in successful_steps
            ),
        )