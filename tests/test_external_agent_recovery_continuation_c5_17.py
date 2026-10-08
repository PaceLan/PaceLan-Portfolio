import unittest

from application.external_agent import ExternalAgentRequest
from application.external_agent_recovery import (
    ExternalAgentRecoveryService,
    ExternalRecoveryResult,
    ExternalRecoveryState,
)
from application.external_agent_recovery_continuation import (
    ExternalAgentRecoveryContinuationService,
    RecoveryContinuationState,
)


class ExternalAgentRecoveryContinuationC517Tests(unittest.TestCase):
    def setUp(self):
        self.service = ExternalAgentRecoveryContinuationService()
        self.request = ExternalAgentRequest(
            task_id="task-1",
            workflow_id="workflow-1",
            payload={"goal": "continue"},
        )

    def test_resumed_recovery_continues_original_chain(self):
        recovery = ExternalRecoveryResult(
            state=ExternalRecoveryState.RESUMED,
            task_id="task-1",
            workflow_id="workflow-1",
            project_id="project-1",
            run_id="run-1",
            task_status="PAUSED",
            run_status="RESUMED",
            recoverable=True,
            message="resumed",
        )

        result = self.service.continue_original(
            self.request,
            recovery,
        )

        self.assertEqual(
            result.state,
            RecoveryContinuationState.CONTINUED,
        )
        self.assertEqual(result.task_id, "task-1")
        self.assertEqual(result.workflow_id, "workflow-1")
        self.assertEqual(result.run_id, "run-1")

    def test_non_resumed_recovery_does_not_continue(self):
        recovery = ExternalRecoveryResult(
            state=ExternalRecoveryState.RECONNECTED,
            task_id="task-1",
            workflow_id="workflow-1",
            project_id="project-1",
            run_id="run-1",
            task_status="RUNNING",
            run_status="RUNNING",
            recoverable=True,
            message="reconnected",
        )

        result = self.service.continue_original(
            self.request,
            recovery,
        )

        self.assertEqual(
            result.state,
            RecoveryContinuationState.NOT_READY,
        )

    def test_task_mismatch_blocks_continuation(self):
        recovery = ExternalRecoveryResult(
            state=ExternalRecoveryState.RESUMED,
            task_id="task-other",
            workflow_id="workflow-1",
            project_id="project-1",
            run_id="run-1",
            task_status="PAUSED",
            run_status="RESUMED",
            recoverable=True,
            message="resumed",
        )

        result = self.service.continue_original(
            self.request,
            recovery,
        )

        self.assertEqual(
            result.state,
            RecoveryContinuationState.BLOCKED,
        )

    def test_workflow_mismatch_blocks_continuation(self):
        recovery = ExternalRecoveryResult(
            state=ExternalRecoveryState.RESUMED,
            task_id="task-1",
            workflow_id="workflow-other",
            project_id="project-1",
            run_id="run-1",
            task_status="PAUSED",
            run_status="RESUMED",
            recoverable=True,
            message="resumed",
        )

        result = self.service.continue_original(
            self.request,
            recovery,
        )

        self.assertEqual(
            result.state,
            RecoveryContinuationState.BLOCKED,
        )


if __name__ == "__main__":
    unittest.main()
