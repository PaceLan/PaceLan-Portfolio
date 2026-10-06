from unittest import TestCase

from agent_workflow.workflow_core import WorkflowStatus, WorkflowStepResult
from agent_workflow.workflow_result import WorkflowResult
from application.execution_verification_trigger import ExecutionVerificationTrigger
from application.models import ResultModel, RunModel
from application.verification import VerificationStatus


class ExecutionVerificationTriggerC48Tests(TestCase):
    def _case(self, status, success, failed=0, blocked=0):
        workflow = WorkflowResult.from_step_results(
            (WorkflowStepResult("step", status, "", success),),
            run_id="run-1",
        )
        run = RunModel(run_id="run-1", task_id="task-1")
        result = ResultModel(
            run_id="run-1",
            status=status.value,
            total_steps=1,
            successful_steps=1 if success else 0,
            failed_steps=failed,
            blocked_steps=blocked,
            completed_successfully=success,
        )
        return ExecutionVerificationTrigger.verify(workflow, run, result)

    def test_success_triggers_verified(self):
        self.assertEqual(
            self._case(WorkflowStatus.COMPLETED, True).status,
            VerificationStatus.VERIFIED,
        )

    def test_failed_triggers_not_verified(self):
        self.assertEqual(
            self._case(WorkflowStatus.FAILED, False, failed=1).status,
            VerificationStatus.NOT_VERIFIED,
        )

    def test_blocked_triggers_blocked(self):
        self.assertEqual(
            self._case(WorkflowStatus.BLOCKED, False, blocked=1).status,
            VerificationStatus.BLOCKED,
        )

    def test_rejects_non_workflow_result(self):
        with self.assertRaises(TypeError):
            ExecutionVerificationTrigger.verify(
                object(),
                RunModel(run_id="run-1", task_id="task-1"),
                ResultModel(run_id="run-1", status="completed"),
            )
