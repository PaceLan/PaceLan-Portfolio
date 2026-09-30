"""Immutable workflow plan definitions and deterministic plan execution."""

from dataclasses import dataclass
from typing import Callable, Tuple

from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.workflow_core import (
    AgentWorkflow,
    WorkflowStatus,
    WorkflowStepResult,
    WorkflowTask,
)
from permissions.reporting import ApprovalStatus, RiskLevel


@dataclass(frozen=True)
class WorkflowStep:
    """Immutable description of one workflow action."""

    operation: str
    action: Callable[[], str]
    risk: RiskLevel = RiskLevel.SAFE
    approval: ApprovalStatus = ApprovalStatus.NOT_REQUESTED
    target: str = "."
    context: str | None = None
    step_id: str = ""


@dataclass(frozen=True)
class WorkflowPlan:
    """Immutable workflow task and ordered execution steps."""

    task: WorkflowTask
    steps: Tuple[WorkflowStep, ...] = ()


def run_plan(
    workflow: AgentWorkflow,
    plan: WorkflowPlan,
    tracker: ExecutionTracker,
) -> tuple[WorkflowStepResult, ...]:
    """Execute a workflow plan while isolating orchestration failures."""
    try:
        workflow.task_status(plan.task.task_id)
    except KeyError:
        workflow.start_task(plan.task)

    results = []

    for index, step in enumerate(plan.steps):
        tracker.start_step(step.step_id)

        try:
            result = workflow.run_step(
                plan.task,
                step.operation,
                step.action,
                risk=step.risk,
                approval=step.approval,
                target=step.target,
                context=step.context,
            )
        except Exception as error:
            result = WorkflowStepResult(
                step.operation,
                WorkflowStatus.FAILED,
                type(error).__name__,
                False,
            )
            tracker.fail_step(step.step_id)

            for remaining_step in plan.steps[index + 1:]:
                tracker.skip_step(remaining_step.step_id)

            tracker.fail_run()
            results.append(result)
            break

        results.append(result)

        if result.success:
            tracker.complete_step(step.step_id)
            continue

        tracker.fail_step(step.step_id)

        for remaining_step in plan.steps[index + 1:]:
            tracker.skip_step(remaining_step.step_id)

        tracker.fail_run()
        break
    else:
        tracker.complete_run()

    return tuple(results)
