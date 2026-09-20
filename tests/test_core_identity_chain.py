import unittest

from agent_workflow.core_adapter import CoreAdapter
from agent_workflow.core_interfaces import (
    Execution,
    Result,
    Run,
    Task,
)
from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.execution_tracking import RunStatus
from agent_workflow.workflow_core import (
    WorkflowStatus,
    WorkflowTask,
    WorkflowStepResult,
)
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_run import WorkflowRunContext


class CoreIdentityChainTests(unittest.TestCase):
    def test_task_to_run_identity_chain(self):
        task = Task(
            task_id="task-001",
            project_id="project-001",
        )

        workflow_task = CoreAdapter.task_to_workflow(task)
        context = WorkflowRunContext.create(workflow_task)
        run = CoreAdapter.context_to_run(context)

        self.assertEqual(run.task_id, task.task_id)
        self.assertEqual(context.task_id, task.task_id)
        self.assertEqual(run.run_id, context.run_id)

    def test_run_to_execution_identity_chain(self):
        run = Run(
            run_id="run-001",
            task_id="task-001",
        )
        context = CoreAdapter.run_to_context(run)
        tracker = ExecutionTracker(
            context,
            ("step-001",),
        )

        execution = CoreAdapter.execution_from_tracker(tracker)

        self.assertIsInstance(execution, Execution)
        self.assertEqual(execution.run_id, run.run_id)
        self.assertEqual(context.run_id, run.run_id)
        self.assertEqual(execution.status, RunStatus.CREATED.value)

    def test_execution_to_result_identity_chain(self):
        context = WorkflowRunContext(
            run_id="run-001",
            task_id="task-001",
        )
        tracker = ExecutionTracker(
            context,
            ("step-001",),
        )

        execution = CoreAdapter.execution_from_tracker(tracker)

        step_result = WorkflowStepResult(
            operation="test",
            status=WorkflowStatus.COMPLETED,
            result="ok",
            success=True,
        )
        workflow_result = WorkflowResult.from_step_results(
            [step_result],
            run_id=execution.run_id,
        )

        result = CoreAdapter.result_from_workflow(
            workflow_result,
            execution.run_id,
        )

        self.assertIsInstance(result, Result)
        self.assertEqual(result.run_id, execution.run_id)
        self.assertEqual(workflow_result.run_id, execution.run_id)

    def test_task_run_execution_result_preserves_identity(self):
        task = Task(
            task_id="task-001",
            project_id="project-001",
        )

        workflow_task = CoreAdapter.task_to_workflow(task)
        context = WorkflowRunContext.create(workflow_task)
        run = CoreAdapter.context_to_run(context)

        tracker = ExecutionTracker(
            context,
            ("step-001",),
        )
        execution = CoreAdapter.execution_from_tracker(tracker)

        step_result = WorkflowStepResult(
            operation="test",
            status=WorkflowStatus.COMPLETED,
            result="ok",
            success=True,
        )
        workflow_result = WorkflowResult.from_step_results(
            [step_result],
            run_id=execution.run_id,
        )
        result = CoreAdapter.result_from_workflow(
            workflow_result,
            execution.run_id,
        )

        self.assertEqual(run.task_id, task.task_id)
        self.assertEqual(run.run_id, context.run_id)
        self.assertEqual(execution.run_id, run.run_id)
        self.assertEqual(result.run_id, execution.run_id)


if __name__ == "__main__":
    unittest.main()