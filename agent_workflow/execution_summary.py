from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_tracking import StepStatus
from agent_workflow.workflow_result import WorkflowResult


@dataclass(frozen=True)
class ExecutionSummary:
    planned_steps: int
    executed_steps: int
    successful_steps: int
    failed_steps: int
    blocked_steps: int
    skipped_steps: int
    first_failure: Optional[int]

    @classmethod
    def from_result_and_snapshot(
        cls,
        result: WorkflowResult,
        snapshot: ExecutionSnapshot,
    ) -> "ExecutionSummary":
        step_states = snapshot.step_states

        planned_steps = len(step_states)

        skipped_steps = sum(
            1
            for state in step_states.values()
            if state is StepStatus.SKIPPED
        )

        executed_steps = sum(
            1
            for state in step_states.values()
            if state in (
                StepStatus.SUCCESS,
                StepStatus.FAILED,
            )
        )

        return cls(
            planned_steps=planned_steps,
            executed_steps=executed_steps,
            successful_steps=result.successful_steps,
            failed_steps=result.failed_steps,
            blocked_steps=result.blocked_steps,
            skipped_steps=skipped_steps,
            first_failure=result.failure_index,
        )