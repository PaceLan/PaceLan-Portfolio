from __future__ import annotations

from threading import RLock

from agent_workflow.workflow_plan import WorkflowPlan
from application.models import PlanModel


class AutonomousPlanBindingService:
    """Bind a stable application Plan to its executable WorkflowPlan."""

    def __init__(self) -> None:
        self._bindings: dict[str, WorkflowPlan] = {}
        self._plans: dict[str, PlanModel] = {}
        self._lock = RLock()

    def bind(
        self,
        plan: PlanModel,
        workflow_plan: WorkflowPlan,
    ) -> PlanModel:
        if not isinstance(plan, PlanModel):
            raise TypeError("plan must be a PlanModel")
        if not isinstance(workflow_plan, WorkflowPlan):
            raise TypeError("workflow_plan must be a WorkflowPlan")

        if plan.task_id != workflow_plan.task.task_id:
            raise ValueError("plan and workflow plan must have the same task_id")

        if plan.project_id != workflow_plan.task.project_id:
            raise ValueError(
                "plan and workflow plan must belong to the same project"
            )

        with self._lock:
            self._bindings[plan.task_id] = workflow_plan
            self._plans[plan.task_id] = plan

        return plan

    def get(self, task_id: str) -> WorkflowPlan:
        if not isinstance(task_id, str) or not task_id:
            raise ValueError("task_id must be a non-empty string")

        with self._lock:
            try:
                return self._bindings[task_id]
            except KeyError as exc:
                raise KeyError(
                    f"No executable plan bound to task_id: {task_id}"
                ) from exc

    def get_for_plan(self, plan: PlanModel) -> WorkflowPlan:
        if not isinstance(plan, PlanModel):
            raise TypeError("plan must be a PlanModel")
        with self._lock:
            try:
                bound_plan = self._plans[plan.task_id]
                workflow_plan = self._bindings[plan.task_id]
            except KeyError as exc:
                raise KeyError(
                    f"No executable plan bound to task_id: {plan.task_id}"
                ) from exc
        if bound_plan != plan:
            raise ValueError(
                'provided plan does not match the bound plan'
            )
        if (
            workflow_plan.task.task_id != plan.task_id
            or workflow_plan.task.project_id != plan.project_id
        ):
            raise ValueError(
                'bound workflow plan identity does not match application plan'
            )
        return workflow_plan

    def remove(self, task_id: str) -> None:
        with self._lock:
            self._bindings.pop(task_id, None)
            self._plans.pop(task_id, None)


__all__ = ["AutonomousPlanBindingService"]
