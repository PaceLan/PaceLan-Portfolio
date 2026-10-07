"""Structured command planning for autonomous execution."""
from dataclasses import dataclass
from typing import Tuple

from agent_workflow.workflow_plan import WorkflowPlan


@dataclass(frozen=True)
class Command:
    task_id: str
    project_id: str
    step_id: str
    operation: str
    target: str = "."
    context: str | None = None


@dataclass(frozen=True)
class CommandPlan:
    task_id: str
    project_id: str
    commands: Tuple[Command, ...] = ()


class CommandPlanner:
    def plan(self, workflow_plan: WorkflowPlan) -> CommandPlan:
        if not isinstance(workflow_plan, WorkflowPlan):
            raise TypeError("workflow_plan must be a WorkflowPlan")

        task = workflow_plan.task
        commands = tuple(
            Command(
                task_id=task.task_id,
                project_id=task.project_id,
                step_id=step.step_id,
                operation=step.operation,
                target=step.target,
                context=step.context,
            )
            for step in workflow_plan.steps
        )
        return CommandPlan(
            task_id=task.task_id,
            project_id=task.project_id,
            commands=commands,
        )
