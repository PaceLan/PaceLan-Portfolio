"""Adapters between unified core interfaces and legacy workflow interfaces."""

from agent_workflow.core_interfaces import (
    Execution,
    Record,
    Result,
    Run,
    Task,
)
from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.workflow_core import WorkflowTask
from agent_workflow.workflow_result import WorkflowResult


class CoreAdapter:
    """Convert between unified core objects and existing workflow objects."""

    @staticmethod
    def task_to_workflow(task: Task) -> WorkflowTask:
        """Convert a unified Task into the legacy WorkflowTask."""
        if not isinstance(task, Task):
            raise TypeError("task must be a Task")

        return WorkflowTask(
            task_id=task.task_id,
            description="",
            context="",
            project_id=task.project_id,
        )

    @staticmethod
    def workflow_task_to_task(
        workflow_task: WorkflowTask,
        project_id: str,
    ) -> Task:
        """Convert a legacy WorkflowTask into a unified Task."""
        if not isinstance(workflow_task, WorkflowTask):
            raise TypeError("workflow_task must be a WorkflowTask")

        if not isinstance(project_id, str) or not project_id:
            raise ValueError("project_id must be a non-empty string")

        return Task(
            task_id=workflow_task.task_id,
            project_id=project_id,
        )

    @staticmethod
    def run_to_context(
        run: Run,
    ):
        """Convert a unified Run into a WorkflowRunContext."""
        from agent_workflow.workflow_run import WorkflowRunContext

        if not isinstance(run, Run):
            raise TypeError("run must be a Run")

        return WorkflowRunContext(
            run_id=run.run_id,
            task_id=run.task_id,
        )

    @staticmethod
    def context_to_run(context) -> Run:
        """Convert a WorkflowRunContext into a unified Run."""
        from agent_workflow.workflow_run import WorkflowRunContext

        if not isinstance(context, WorkflowRunContext):
            raise TypeError("context must be a WorkflowRunContext")

        return Run(
            run_id=context.run_id,
            task_id=context.task_id,
        )

    @staticmethod
    def execution_from_tracker(
        tracker: ExecutionTracker,
    ) -> Execution:
        """Convert the current tracker state into a unified Execution."""
        if not isinstance(tracker, ExecutionTracker):
            raise TypeError("tracker must be an ExecutionTracker")

        return Execution(
            run_id=tracker.context.run_id,
            status=tracker.run_status.value,
        )

    @staticmethod
    def result_from_workflow(
        workflow_result: WorkflowResult,
        run_id: str,
    ) -> Result:
        """Convert a WorkflowResult into a unified Result."""
        if not isinstance(workflow_result, WorkflowResult):
            raise TypeError("workflow_result must be a WorkflowResult")

        if not isinstance(run_id, str) or not run_id:
            raise ValueError("run_id must be a non-empty string")

        return Result(
            run_id=run_id,
            status=workflow_result.status.value,
        )

    @staticmethod
    def record_from_operation(
        record_id: str,
        project_id: str,
        run_id: str,
    ) -> Record:
        """Create a unified Record identity for an operation record."""
        if not isinstance(record_id, str) or not record_id:
            raise ValueError("record_id must be a non-empty string")

        if not isinstance(project_id, str) or not project_id:
            raise ValueError("project_id must be a non-empty string")

        if not isinstance(run_id, str) or not run_id:
            raise ValueError("run_id must be a non-empty string")

        return Record(
            record_id=record_id,
            project_id=project_id,
            run_id=run_id,
        )