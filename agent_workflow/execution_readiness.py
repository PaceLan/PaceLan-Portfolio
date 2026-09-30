"""Deterministic execution-readiness analysis for workflow plans."""

from dataclasses import dataclass
from typing import Tuple

from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from permissions.reporting import ApprovalStatus, RiskLevel


@dataclass(frozen=True)
class ExecutionReadinessResult:
    """Immutable result of checking whether a workflow plan is ready."""

    ready: bool
    issues: Tuple[str, ...] = ()
    warnings: Tuple[str, ...] = ()
    checked_step_ids: Tuple[str, ...] = ()


class ExecutionReadiness:
    """Check execution prerequisites without executing or mutating a plan."""

    def check(self, plan: WorkflowPlan) -> ExecutionReadinessResult:
        """Return deterministic readiness information for a workflow plan."""
        if not isinstance(plan, WorkflowPlan):
            raise TypeError("plan must be a WorkflowPlan")

        issues: list[str] = []
        warnings: list[str] = []
        checked_step_ids: list[str] = []

        if not plan.task.task_id:
            issues.append("task_id must not be empty")

        seen_step_ids: set[str] = set()

        for index, step in enumerate(plan.steps, start=1):
            fallback_id = f"step-{index:03d}"

            if not isinstance(step, WorkflowStep):
                issues.append(f"{fallback_id}: must be a WorkflowStep")
                continue

            step_id = step.step_id

            if step_id:
                checked_step_ids.append(step_id)

                if step_id in seen_step_ids:
                    issues.append(f"{step_id}: duplicate step_id")
                else:
                    seen_step_ids.add(step_id)
            else:
                issues.append(f"{fallback_id}: step_id must not be empty")

            effective_id = step_id or fallback_id

            if not step.operation:
                issues.append(
                    f"{effective_id}: operation must not be empty"
                )

            if not callable(step.action):
                issues.append(
                    f"{effective_id}: action must be callable"
                )

            if not isinstance(step.risk, RiskLevel):
                issues.append(
                    f"{effective_id}: risk must be a RiskLevel"
                )

            if not isinstance(step.approval, ApprovalStatus):
                issues.append(
                    f"{effective_id}: approval must be an ApprovalStatus"
                )

            if (
                isinstance(step.approval, ApprovalStatus)
                and step.approval
                in {
                    ApprovalStatus.DENIED,
                    ApprovalStatus.BLOCKED,
                }
            ):
                warnings.append(
                    f"{effective_id}: "
                    f"approval is {step.approval.value}"
                )

        return ExecutionReadinessResult(
            ready=not issues,
            issues=tuple(issues),
            warnings=tuple(warnings),
            checked_step_ids=tuple(checked_step_ids),
        )
