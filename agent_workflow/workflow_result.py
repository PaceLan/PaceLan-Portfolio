"""Immutable observation and reporting for completed workflow results."""

from dataclasses import dataclass
from typing import Tuple

from agent_workflow.workflow_core import WorkflowStatus, WorkflowStepResult


@dataclass(frozen=True)
class WorkflowResult:
    """Immutable, deterministic observation of one workflow execution."""

    step_results: Tuple[WorkflowStepResult, ...]
    status: WorkflowStatus
    total_steps: int
    successful_steps: int
    failed_steps: int
    blocked_steps: int
    completed_successfully: bool
    failure_index: int | None
    run_id: str = ""

    @classmethod
    def from_step_results(
        cls,
        step_results: tuple[WorkflowStepResult, ...]
        | list[WorkflowStepResult],
        run_id: str = "",
    ) -> "WorkflowResult":
        """Build a stable observation without executing or modifying anything."""
        results = tuple(step_results)

        if not all(isinstance(result, WorkflowStepResult) for result in results):
            raise TypeError("step_results must contain WorkflowStepResult instances")

        if not isinstance(run_id, str):
            raise TypeError("run_id must be a string")

        total_steps = len(results)
        successful_steps = sum(1 for result in results if result.success)
        failed_steps = sum(
            1
            for result in results
            if result.status is WorkflowStatus.FAILED
        )
        blocked_steps = sum(
            1
            for result in results
            if result.status is WorkflowStatus.BLOCKED
        )

        failure_index = next(
            (
                index
                for index, result in enumerate(results)
                if not result.success
            ),
            None,
        )

        if not results:
            status = WorkflowStatus.RECEIVED
        else:
            status = results[-1].status

        completed_successfully = (
            bool(results)
            and all(result.success for result in results)
            and status is WorkflowStatus.COMPLETED
        )

        return cls(
            step_results=results,
            status=status,
            total_steps=total_steps,
            successful_steps=successful_steps,
            failed_steps=failed_steps,
            blocked_steps=blocked_steps,
            completed_successfully=completed_successfully,
            failure_index=failure_index,
            run_id=run_id,
        )

    @property
    def failed_step(self) -> WorkflowStepResult | None:
        """Return the first unsuccessful step, if one exists."""
        if self.failure_index is None:
            return None
        return self.step_results[self.failure_index]

    def summary(self) -> str:
        """Return a deterministic human-readable observation summary."""
        failure_text = (
            "None"
            if self.failure_index is None
            else str(self.failure_index + 1)
        )

        return "\n".join(
            [
                "WORKFLOW RESULT",
                f"Status: {self.status.value}",
                f"Total steps: {self.total_steps}",
                f"Successful steps: {self.successful_steps}",
                f"Failed steps: {self.failed_steps}",
                f"Blocked steps: {self.blocked_steps}",
                f"Completed successfully: {self.completed_successfully}",
                f"Failure step: {failure_text}",
            ]
        )