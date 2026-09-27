from collections.abc import Iterable
from dataclasses import dataclass

from agent_workflow.context_understanding import (
    ContextUnderstandingResult,
)
from agent_workflow.execution_snapshot import ExecutionSnapshot
from agent_workflow.execution_summary import ExecutionSummary
from agent_workflow.project_context_interface import ProjectContextAgentInterface
from agent_workflow.result_analysis import WorkflowResultAnalysis
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_run import WorkflowRunContext
from agent_workflow.workflow_service import WorkflowService


@dataclass(frozen=True)
class AgentExecution:
    task: WorkflowTask
    plan: WorkflowPlan
    run_context: WorkflowRunContext
    result: WorkflowResult
    analysis: WorkflowResultAnalysis
    snapshot: ExecutionSnapshot
    summary: ExecutionSummary
    project_context_agent: ProjectContextAgentInterface | None = None
    context_understanding: ContextUnderstandingResult | None = None


class AgentService:
    """High-level orchestration facade for one complete agent execution."""

    def __init__(
        self,
        workflow_service: WorkflowService,
        project_context_agent: ProjectContextAgentInterface | None = None,
    ) -> None:
        if not isinstance(workflow_service, WorkflowService):
            raise TypeError("workflow_service must be a WorkflowService")

        if (
            project_context_agent is not None
            and not isinstance(
                project_context_agent,
                ProjectContextAgentInterface,
            )
        ):
            raise TypeError(
                "project_context_agent must be a "
                "ProjectContextAgentInterface"
            )

        self.workflow_service = workflow_service
        self.project_context_agent = project_context_agent

    def run(
        self,
        task: WorkflowTask,
        steps: Iterable[WorkflowStep] = (),
    ) -> AgentExecution:
        if not isinstance(task, WorkflowTask):
            raise TypeError("task must be a WorkflowTask")

        context_understanding = None

        if self.project_context_agent is not None:
            context_understanding = (
                self.project_context_agent
                .context_understanding
                .understand_task(task)
            )

        plan = self.workflow_service.build(task, steps)
        result = self.workflow_service.execute(plan)

        run_context = self.workflow_service.last_run_context
        tracker = self.workflow_service.last_execution_tracker

        if run_context is None:
            raise RuntimeError(
                "workflow execution did not establish run context"
            )

        if tracker is None:
            raise RuntimeError(
                "workflow execution did not establish tracker"
            )

        snapshot = tracker.snapshot()
        analysis = WorkflowResultAnalysis.from_result(result)
        summary = ExecutionSummary.from_result_and_snapshot(
            result,
            snapshot,
        )

        return AgentExecution(
    task=task,
    plan=plan,
    run_context=run_context,
    result=result,
    analysis=analysis,
    snapshot=snapshot,
    summary=summary,
    project_context_agent=self.project_context_agent,
    context_understanding=context_understanding,
)