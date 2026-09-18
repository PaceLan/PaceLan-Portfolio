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

    for step in plan.steps:
        if not isinstance(step, WorkflowStep):
            raise TypeError("Workflow plan steps must be WorkflowStep instances")
        if not step.operation:
            raise ValueError("Workflow step operation must not be empty")

    return plan


def build_plan(
    task: WorkflowTask,
    steps: Iterable[WorkflowStep] = (),
) -> WorkflowPlan:
    """Build and validate an immutable workflow plan.

    This function only constructs a plan. It never executes an action,
    modifies the project, or bypasses permission/approval handling.
    """
    if not isinstance(task, WorkflowTask):
        raise TypeError("task must be a WorkflowTask")

    step_tuple: Tuple[WorkflowStep, ...] = tuple(steps)

    for step in step_tuple:
        if not isinstance(step, WorkflowStep):
            raise TypeError("steps must contain WorkflowStep instances")

    plan = WorkflowPlan(task=task, steps=step_tuple)
    return validate_plan(plan)
