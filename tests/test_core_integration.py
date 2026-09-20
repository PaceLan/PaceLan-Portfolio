import unittest

from agent_workflow.core_adapter import CoreAdapter
from agent_workflow.core_interfaces import (
    Execution,
    Project,
    Record,
    Result,
    Run,
    Task,
)
from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.workflow_core import (
    WorkflowStatus,
    WorkflowStepResult,
    WorkflowTask,
)
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_run import WorkflowRunContext


class CoreIntegrationTests(unittest.TestCase):
    def test_project_task_run_relationship(self):
        project = Project(project_id="project-1")

        task = Task(
            task_id="task-1",
            project_id=project.project_id,
        )

        run = Run(
            run_id="run-1",
            task_id=task.task_id,
        )

        self.assertEqual(task.project_id, project.project_id)
        self.assertEqual(run.task_id, task.task_id)

    def test_unified_core_to_workflow_and_back(self):
        task = Task(
            task_id="task-1",
            project_id="project-1",
        )

        workflow_task = CoreAdapter.task_to_workflow(task)

        self.assertEqual(workflow_task.task_id, task.task_id)

        context = WorkflowRunContext.create(workflow_task)

        run = CoreAdapter.context_to_run(context)

        self.assertEqual(run.run_id, context.run_id)
        self.assertEqual(run.task_id, task.task_id)

        tracker = ExecutionTracker(
            context,
            ("step-1",),
        )

        execution = CoreAdapter.execution_from_tracker(tracker)

        self.assertIsInstance(execution, Execution)
        self.assertEqual(execution.run_id, run.run_id)

        step_result = WorkflowStepResult(
            operation="step-1",
            status=WorkflowStatus.COMPLETED,
            result="ok",
            success=True,
        )

        workflow_result = WorkflowResult.from_step_results([step_result])

        result = CoreAdapter.result_from_workflow(
            workflow_result,
            run.run_id,
        )

        self.assertIsInstance(result, Result)
        self.assertEqual(result.run_id, run.run_id)
        self.assertEqual(
            result.status,
            workflow_result.status.value,
        )

        record = CoreAdapter.record_from_operation(
            "record-1",
            task.project_id,
            run.run_id,
        )

        self.assertIsInstance(record, Record)
        self.assertEqual(record.project_id, task.project_id)
        self.assertEqual(record.run_id, run.run_id)

    def test_task_identity_is_preserved_through_core_conversion(self):
        task = Task(
            task_id="task-identity",
            project_id="project-identity",
        )

        workflow_task = CoreAdapter.task_to_workflow(task)

        converted_task = CoreAdapter.workflow_task_to_task(
            workflow_task,
            task.project_id,
        )

        self.assertEqual(converted_task.task_id, task.task_id)
        self.assertEqual(converted_task.project_id, task.project_id)

    def test_run_identity_is_preserved_through_core_conversion(self):
        run = Run(
            run_id="run-identity",
            task_id="task-identity",
        )

        context = CoreAdapter.run_to_context(run)
        converted_run = CoreAdapter.context_to_run(context)

        self.assertEqual(converted_run.run_id, run.run_id)
        self.assertEqual(converted_run.task_id, run.task_id)


if __name__ == "__main__":
    unittest.main()