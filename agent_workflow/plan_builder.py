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
            raise TypeError(
                "Workflow plan steps must be WorkflowStep instances"
            )

        if not step.operation:
            raise ValueError(
                "Workflow step operation must not be empty"
            )

        if not callable(step.action):
            raise TypeError(
                f"Workflow step {index} action must be callable"
            )

        if not step.step_id:
            raise ValueError(
                f"Workflow step {index} must have a non-empty step ID"
            )

    step_ids = [step.step_id for step in plan.steps]

    if len(step_ids) != len(set(step_ids)):
        raise ValueError(
            "Workflow step IDs must not contain duplicates"
        )

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
            raise TypeError(
                "steps must contain WorkflowStep instances"
            )

    used_step_ids = {
        step.step_id
        for step in step_tuple
        if step.step_id
    }

    normalized_steps = []
    next_step_number = 1

    for step in step_tuple:
        step_id = step.step_id

        if not step_id:
            while f"step-{next_step_number:03d}" in used_step_ids:
                next_step_number += 1

            step_id = f"step-{next_step_number:03d}"
            used_step_ids.add(step_id)
            next_step_number += 1

        normalized_steps.append(
            WorkflowStep(
                operation=step.operation,
                action=step.action,
                risk=step.risk,
                approval=step.approval,
                target=step.target,
                context=step.context,
                step_id=step_id,
            )
        )

    plan = WorkflowPlan(
        task=task,
        steps=tuple(normalized_steps),
    )

    return validate_plan(plan)
