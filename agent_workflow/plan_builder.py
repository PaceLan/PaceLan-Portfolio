"""Pure workflow plan construction and validation helpers."""

from collections.abc import Iterable
from typing import Tuple

from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep


def validate_plan(plan: WorkflowPlan) -> WorkflowPlan:
    """Validate an existing workflow plan without executing anything."""
    if not isinstance(plan, WorkflowPlan):
        raise TypeError("plan must be a WorkflowPlan")

    if not plan.task.task_id:
        raise ValueError("Workflow plan task ID must not be empty")

    for index, step in enumerate(plan.steps, start=1):
        if not isinstance(step, WorkflowStep):
            raise TypeError("Workflow plan steps must be WorkflowStep instances")
        if not step.operation:
            raise ValueError("Workflow step operation must not be empty")
        if not step.step_id:
            raise ValueError(
                f"Workflow step {index} must have a non-empty step ID"
            )

    step_ids = [step.step_id for step in plan.steps]

    if len(step_ids) != len(set(step_ids)):
        raise ValueError("Workflow step IDs must not contain duplicates")

    return plan


def build_plan(
    task: WorkflowTask,
    steps: Iterable[WorkflowStep] = (),
) -> WorkflowPlan:
    """Build and validate an immutable workflow plan."""
    if not isinstance(task, WorkflowTask):
        raise TypeError("task must be a WorkflowTask")

    step_tuple: Tuple[WorkflowStep, ...] = tuple(steps)

    for step in step_tuple:
        if not isinstance(step, WorkflowStep):
            raise TypeError("steps must contain WorkflowStep instances")

    normalized_steps = tuple(
        WorkflowStep(
            operation=step.operation,
            action=step.action,
            risk=step.risk,
            approval=step.approval,
            target=step.target,
            context=step.context,
            step_id=step.step_id or f"step-{index:03d}",
        )
        for index, step in enumerate(step_tuple, start=1)
    )

    plan = WorkflowPlan(
        task=task,
        steps=normalized_steps,
    )

    return validate_plan(plan)