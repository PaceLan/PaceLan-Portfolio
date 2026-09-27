"""High-level orchestration facade for Agent Workflow execution."""

from collections.abc import Iterable

from agent_workflow.execution_readiness import ExecutionReadiness
from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.plan_builder import build_plan
from agent_workflow.risk_approval import ExecutionReadinessGate
from agent_workflow.workflow_core import (
    AgentWorkflow,
    WorkflowStatus,
    WorkflowStepResult,
    WorkflowTask,
)
from agent_workflow.workflow_plan import WorkflowPlan, WorkflowStep, run_plan
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_run import WorkflowRunContext


class WorkflowService:
    def __init__(self, workflow: AgentWorkflow) -> None:
        if not isinstance(workflow, AgentWorkflow):
            raise TypeError("workflow must be an AgentWorkflow")
        self.workflow = workflow
        self._last_run_context: WorkflowRunContext | None = None
        self._last_execution_tracker: ExecutionTracker | None = None

    @property
    def last_run_context(self) -> WorkflowRunContext | None:
        return self._last_run_context

    @property
    def last_execution_tracker(self) -> ExecutionTracker | None:
        return self._last_execution_tracker

    def build(
        self,
        task: WorkflowTask,
        steps: Iterable[WorkflowStep] = (),
    ) -> WorkflowPlan:
        return build_plan(task, steps)

    def execute(self, plan: WorkflowPlan) -> WorkflowResult:
        if not isinstance(plan, WorkflowPlan):
            raise TypeError("plan must be a WorkflowPlan")

        validated_plan = build_plan(
            plan.task,
            plan.steps,
        )

        readiness = ExecutionReadiness().check(validated_plan)

        if not readiness.ready:
            raise ValueError(
                "workflow execution readiness check failed: "
                + "; ".join(readiness.issues)
            )

        gate_assessments = ExecutionReadinessGate.assess_plan(
            validated_plan.steps,
        )

        blocked = tuple(
            assessment
            for assessment in gate_assessments
            if not assessment.is_ready
        )

        self._last_run_context = WorkflowRunContext.create(
            validated_plan.task
        )

        tracker = ExecutionTracker(
            self._last_run_context,
            tuple(step.step_id for step in validated_plan.steps),
        )
        self._last_execution_tracker = tracker
        tracker.start_run()

        if blocked:
            results: list[WorkflowStepResult] = []

            try:
                self.workflow.task_status(validated_plan.task.task_id)
            except KeyError:
                self.workflow.start_task(validated_plan.task)

            for index, step in enumerate(validated_plan.steps):
                assessment = next(
                    (
                        item
                        for item in gate_assessments
                        if item.step_id == step.step_id
                    ),
                    None,
                )

                if assessment is not None and not assessment.is_ready:
                    tracker.start_step(step.step_id)

                    result = WorkflowStepResult(
                        step.operation,
                        WorkflowStatus.BLOCKED,
                        assessment.reason,
                        False,
                    )

                    tracker.fail_step(step.step_id)
                    results.append(result)

                    for remaining_step in validated_plan.steps[
                        index + 1:
                    ]:
                        tracker.skip_step(remaining_step.step_id)

                    tracker.fail_run()
                    break

                tracker.start_step(step.step_id)

                try:
                    result = self.workflow.run_step(
                        validated_plan.task,
                        step.operation,
                        step.action,
                        risk=step.risk,
                        approval=step.approval,
                        target=step.target,
                        context=step.context,
                    )
                except Exception as error:
                    result = WorkflowStepResult(
                        step.operation,
                        WorkflowStatus.FAILED,
                        type(error).__name__,
                        False,
                    )

                    tracker.fail_step(step.step_id)

                    for remaining_step in validated_plan.steps[
                        index + 1:
                    ]:
                        tracker.skip_step(remaining_step.step_id)

                    tracker.fail_run()
                    results.append(result)
                    break

                results.append(result)

                if result.success:
                    tracker.complete_step(step.step_id)
                    continue

                tracker.fail_step(step.step_id)

                for remaining_step in validated_plan.steps[
                    index + 1:
                ]:
                    tracker.skip_step(remaining_step.step_id)

                tracker.fail_run()
                break

            return WorkflowResult.from_step_results(
                results,
                run_id=self._last_run_context.run_id,
            )

        step_results = run_plan(
            self.workflow,
            validated_plan,
            tracker,
        )

        return WorkflowResult.from_step_results(
            step_results,
            run_id=self._last_run_context.run_id,
        )
