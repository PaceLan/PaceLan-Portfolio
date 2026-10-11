"""Deterministic planning from Agent project context."""

from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path

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

        supplied_steps = tuple(steps)

        if supplied_steps:
            enriched_steps = tuple(
                self._enrich_step(step, project_context)
                for step in supplied_steps
            )
            return build_plan(task, enriched_steps)

        context = self.project_context_agent.context_understanding.understand(
            task,
            fallback_to_first_file=True,
        )
        plan = self.planner_intelligence.plan(task, context)
        return self._bind_generated_steps(plan)

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

        supplied_steps = tuple(steps)
        plan = self.planner_intelligence.plan(
            task,
            context,
            supplied_steps,
        )
        if supplied_steps:
            return plan
        return self._bind_generated_steps(plan)

    def _bind_generated_steps(
        self,
        plan: WorkflowPlan,
    ) -> WorkflowPlan:
        """Bind generated plans to real read-only project operations."""
        bound_steps = []

        for step in plan.steps:
            def action(
                operation=step.operation,
                target=step.target,
            ) -> str:
                return self._execute_project_operation(operation, target)

            bound_steps.append(replace(step, action=action))

        return WorkflowPlan(task=plan.task, steps=tuple(bound_steps))

    def _execute_project_operation(
        self,
        operation: str,
        target: str,
    ) -> str:
        """Execute one validated read-only operation at workflow runtime."""
        path = Path(target)

        if path.is_absolute() or ".." in path.parts or str(path) == ".":
            raise ValueError(f"invalid project-relative target: {target}")

        query = self.project_context_agent.query
        project_file = query.get_file(path)
        if project_file is None:
            raise FileNotFoundError(f"project file not found: {target}")

        if operation == "inspect":
            return (
                f"File: {project_file.relative_path}; "
                f"extension={project_file.extension}; "
                f"size={project_file.size}"
            )

        if operation == "analyze":
            ast_result = query.get_python_ast(path)
            if ast_result is None:
                raise ValueError(f"Python AST unavailable for: {target}")
            relationships = query.get_python_relationships(path)
            relationship_count = (
                len(relationships.relationships)
                if relationships is not None
                else 0
            )
            return (
                f"Analysis: {path}; imports={len(ast_result.imports)}; "
                f"classes={len(ast_result.classes)}; "
                f"functions={len(ast_result.functions)}; "
                f"relationships={relationship_count}"
            )

        if operation == "trace_dependencies":
            ast_result = query.get_python_ast(path)
            if ast_result is None:
                raise ValueError(
                    f"Python dependency data unavailable for: {target}"
                )
            dependencies = query.dependency_targets(path)
            if not dependencies:
                return f"Dependencies for {path}: none"
            return f"Dependencies for {path}: {', '.join(dependencies)}"

        raise ValueError(f"unsupported project operation: {operation}")

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