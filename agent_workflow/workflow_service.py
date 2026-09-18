"""High-level orchestration facade for Agent Workflow execution."""

from collections.abc import Iterable

from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.plan_builder import build_plan, validate_plan
from agent_workflow.workflow_core import AgentWorkflow, WorkflowTask
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep, run_plan
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_run import WorkflowRunContext


class WorkflowService:
    """Thin orchestration facade over the existing workflow components."""

    def __init__(self, workflow: AgentWorkflow) -> None:
        if not isinstance(workflow, AgentWorkflow):
            raise TypeError("workflow must be an AgentWorkflow")
        self.workflow = workflow
        self._last_run_context: WorkflowRunContext | None = None
        self._last_execution_tracker: ExecutionTracker | None = None

    @property
    def last_run_context(self) -> WorkflowRunContext | None:
        """Return the context of the most recent accepted workflow run."""
        return self._last_run_context

    @property
    def last_execution_tracker(self) -> ExecutionTracker | None:
        """Return the tracker of the most recent accepted workflow run."""
        return self._last_execution_tracker

    def build(
        self,
        task: WorkflowTask,
        steps: Iterable[WorkflowStep] = (),
    ) -> WorkflowPlan:
        """Build and validate a workflow plan without executing actions."""
        return build_plan(task, steps)

    def execute(self, plan: WorkflowPlan) -> WorkflowResult:
        """Execute an existing plan through the established workflow path."""
        validated_plan = validate_plan(plan)

        self._last_run_context = WorkflowRunContext.create(
            validated_plan.task
        )

        tracker = ExecutionTracker(
            self._last_run_context,
            tuple(step.operation for step in validated_plan.steps),
        )
        self._last_execution_tracker = tracker
        tracker.start_run()

        step_results = run_plan(
            self.workflow,
            validated_plan,
            tracker,
        )

        return WorkflowResult.from_step_results(step_results)