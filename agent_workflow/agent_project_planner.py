"""Deterministic planning from Agent project context."""

from collections.abc import Iterable

from agent_workflow.context_understanding import ContextUnderstandingResult
from agent_workflow.plan_builder import build_plan
from agent_workflow.planner_intelligence import PlannerIntelligence
from agent_workflow.project_context_interface import (
    ProjectContextAgentInterface,
)
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep


class AgentProjectPlanner:
    """Build workflow plans with stable project-context information."""

    def __init__(
        self,
        project_context_agent: ProjectContextAgentInterface,
    ) -> None:
        if not isinstance(
            project_context_agent,
            ProjectContextAgentInterface,
        ):
            raise TypeError(
                "project_context_agent must be a "
                "ProjectContextAgentInterface"
            )

        self.project_context_agent = project_context_agent
        self.planner_intelligence = PlannerIntelligence()

    def build(
        self,
        task: WorkflowTask,
        steps: Iterable[WorkflowStep] = (),
    ) -> WorkflowPlan:
        if not isinstance(task, WorkflowTask):
            raise TypeError("task must be a WorkflowTask")

        summary = self.project_context_agent.project_summary

        project_context = (
            f"project_root={summary.root_path}; "
            f"total_files={summary.total_files}; "
            f"python_files={summary.python_files}"
        )

        enriched_steps = tuple(
            self._enrich_step(step, project_context)
            for step in steps
        )

        return build_plan(
            task,
            enriched_steps,
        )

    def build_from_context(
        self,
        task: WorkflowTask,
        context: ContextUnderstandingResult,
        steps: Iterable[WorkflowStep] = (),
    ) -> WorkflowPlan:
        """Build a deterministic plan from M14 context understanding."""

        if not isinstance(task, WorkflowTask):
            raise TypeError("task must be a WorkflowTask")

        if not isinstance(
            context,
            ContextUnderstandingResult,
        ):
            raise TypeError(
                "context must be a ContextUnderstandingResult"
            )

        return self.planner_intelligence.plan(
            task,
            context,
            steps,
        )

    @staticmethod
    def _enrich_step(
        step: WorkflowStep,
        project_context: str,
    ) -> WorkflowStep:
        if not isinstance(step, WorkflowStep):
            raise TypeError(
                "steps must contain WorkflowStep instances"
            )

        context = (
            project_context
            if step.context is None
            else f"{step.context}; {project_context}"
        )

        return WorkflowStep(
            operation=step.operation,
            action=step.action,
            risk=step.risk,
            approval=step.approval,
            target=step.target,
            context=context,
            step_id=step.step_id,
        )
