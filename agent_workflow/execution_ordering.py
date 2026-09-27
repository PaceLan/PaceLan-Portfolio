"""Deterministic workflow execution ordering."""

from agent_workflow.step_dependency import StepDependencyAwareness
from agent_workflow.workflow_plan import WorkflowPlan


class ExecutionOrdering:
    """Resolve a workflow plan into deterministic executable order."""

    def __init__(
        self,
        dependency_awareness: StepDependencyAwareness | None = None,
    ) -> None:
        self.dependency_awareness = (
            dependency_awareness or StepDependencyAwareness()
        )

    def order(
        self,
        plan: WorkflowPlan,
        dependencies: dict[str, tuple[str, ...]] | None = None,
    ) -> WorkflowPlan:
        if not isinstance(plan, WorkflowPlan):
            raise TypeError("plan must be a WorkflowPlan")

        analysis = self.dependency_awareness.analyze(
            plan,
            dependencies,
        )

        if analysis.issues:
            raise ValueError(
                "workflow execution ordering failed: "
                + "; ".join(analysis.issues)
            )

        steps_by_id = {
            step.step_id: step
            for step in plan.steps
        }

        ordered_steps = tuple(
            steps_by_id[step_id]
            for step_id in analysis.execution_order
        )

        return WorkflowPlan(
            task=plan.task,
            steps=ordered_steps,
        )
