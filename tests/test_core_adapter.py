import unittest

from agent_workflow.core_adapter import CoreAdapter
from agent_workflow.core_interfaces import (
    Execution,
    Record,
    Result,
    Run,
    Task,
)
from agent_workflow.execution_tracking import RunStatus
from agent_workflow.execution_tracker import ExecutionTracker
from agent_workflow.workflow_core import WorkflowStatus, WorkflowTask, WorkflowStepResult
from agent_workflow.workflow_result import WorkflowResult
from agent_workflow.workflow_run import WorkflowRunContext


class CoreAdapterTests(unittest.TestCase):
    def test_task_to_workflow(self):
        task = Task(
            task_id="task-1",
            project_id="project-1",
        )

        result = CoreAdapter.task_to_workflow(task)

        self.assertIsInstance(result, WorkflowTask)
        self.assertEqual(result.task_id, "task-1")

    def test_workflow_task_to_task(self):
        workflow_task = WorkflowTask(
            task_id="task-1",
            description="Build feature",
            context="test context",
        )

        result = CoreAdapter.workflow_task_to_task(
            workflow_task,
            "project-1",
        )

        self.assertIsInstance(result, Task)
        self.assertEqual(result.task_id, "task-1")
        self.assertEqual(result.project_id, "project-1")

    def test_run_to_context(self):
        run = Run(
            run_id="run-1",
            task_id="task-1",
        )

        result = CoreAdapter.run_to_context(run)

        self.assertIsInstance(result, WorkflowRunContext)
        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.task_id, "task-1")

    def test_context_to_run(self):
        context = WorkflowRunContext(
            run_id="run-1",
            task_id="task-1",
        )

        result = CoreAdapter.context_to_run(context)

        self.assertIsInstance(result, Run)
        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.task_id, "task-1")

    def test_execution_from_tracker(self):
        context = WorkflowRunContext(
            run_id="run-1",
            task_id="task-1",
        )
        tracker = ExecutionTracker(
            context,
            ("step-1",),
        )

        result = CoreAdapter.execution_from_tracker(tracker)

        self.assertIsInstance(result, Execution)
        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.status, RunStatus.CREATED.value)

    def test_result_from_workflow(self):
        step_result = WorkflowStepResult(
            operation="test",
            status=WorkflowStatus.COMPLETED,
            result="ok",
            success=True,
        )
        workflow_result = WorkflowResult.from_step_results([step_result])

        result = CoreAdapter.result_from_workflow(
            workflow_result,
            "run-1",
        )

        self.assertIsInstance(result, Result)
        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.status, WorkflowStatus.COMPLETED.value)

    def test_record_from_operation(self):
        result = CoreAdapter.record_from_operation(
            "record-1",
            "project-1",
            "run-1",
        )

        self.assertIsInstance(result, Record)
        self.assertEqual(result.record_id, "record-1")
        self.assertEqual(result.project_id, "project-1")
        self.assertEqual(result.run_id, "run-1")

    def test_workflow_task_conversion_requires_project_id(self):
        workflow_task = WorkflowTask(
            task_id="task-1",
            description="Build feature",
        )

        with self.assertRaises(ValueError):
            CoreAdapter.workflow_task_to_task(
                workflow_task,
                "",
            )

    def test_result_conversion_requires_run_id(self):
        workflow_result = WorkflowResult.from_step_results([])

        with self.assertRaises(ValueError):
            CoreAdapter.result_from_workflow(
                workflow_result,
                "",
            )

    def test_record_conversion_requires_run_id(self):
        with self.assertRaises(ValueError):
            CoreAdapter.record_from_operation(
                "record-1",
                "project-1",
                "",
            )


if __name__ == "__main__":
    unittest.main()