import unittest

from application.recovery_failure_escalation import (
    RecoveryEscalationDecision,
    RecoveryEscalationLevel,
    RecoveryFailureEscalationService,
)


class RecoveryFailureEscalationC518Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.service = RecoveryFailureEscalationService()

    def test_level1_continues_when_retry_available(self) -> None:
        result = self.service.decide(
            level=RecoveryEscalationLevel.LEVEL_1,
            task_id="task-1",
            workflow_id="workflow-1",
            run_id="run-1",
            recoverable=True,
            retry_exhausted=False,
            reason="connection can still be retried",
        )
        self.assertEqual(
            result.decision,
            RecoveryEscalationDecision.CONTINUE,
        )
        self.assertEqual(
            result.current_level,
            RecoveryEscalationLevel.LEVEL_1,
        )
        self.assertIsNone(result.next_level)

    def test_level1_exhaustion_escalates_to_level2(self) -> None:
        result = self.service.decide(
            level=RecoveryEscalationLevel.LEVEL_1,
            task_id="task-1",
            workflow_id="workflow-1",
            run_id="run-1",
            recoverable=True,
            retry_exhausted=True,
            reason="level 1 retries exhausted",
        )
        self.assertEqual(
            result.decision,
            RecoveryEscalationDecision.ESCALATE,
        )
        self.assertEqual(
            result.next_level,
            RecoveryEscalationLevel.LEVEL_2,
        )

    def test_level2_exhaustion_escalates_to_level3(self) -> None:
        result = self.service.decide(
            level=RecoveryEscalationLevel.LEVEL_2,
            task_id="task-1",
            workflow_id="workflow-1",
            run_id="run-1",
            recoverable=True,
            retry_exhausted=True,
            reason="timed recovery exhausted",
        )
        self.assertEqual(
            result.decision,
            RecoveryEscalationDecision.ESCALATE,
        )
        self.assertEqual(
            result.next_level,
            RecoveryEscalationLevel.LEVEL_3,
        )

    def test_level3_requires_user(self) -> None:
        result = self.service.decide(
            level=RecoveryEscalationLevel.LEVEL_3,
            task_id="task-1",
            workflow_id="workflow-1",
            run_id="run-1",
            recoverable=True,
            retry_exhausted=True,
            reason="automatic recovery cannot continue",
        )
        self.assertEqual(
            result.decision,
            RecoveryEscalationDecision.WAITING_FOR_USER,
        )
        self.assertIsNone(result.next_level)

    def test_nonrecoverable_escalates_directly_to_user(self) -> None:
        result = self.service.decide(
            level=RecoveryEscalationLevel.LEVEL_1,
            task_id="task-1",
            workflow_id="workflow-1",
            run_id="run-1",
            recoverable=False,
            retry_exhausted=False,
            reason="state cannot be safely verified",
        )
        self.assertEqual(
            result.decision,
            RecoveryEscalationDecision.WAITING_FOR_USER,
        )
        self.assertEqual(
            result.next_level,
            RecoveryEscalationLevel.LEVEL_3,
        )

    def test_external_wait_is_not_escalated_to_user(self) -> None:
        result = self.service.decide(
            level=RecoveryEscalationLevel.LEVEL_2,
            task_id="task-1",
            workflow_id="workflow-1",
            run_id="run-1",
            recoverable=True,
            retry_exhausted=True,
            reason="external condition is pending",
            waiting_external=True,
        )
        self.assertEqual(
            result.decision,
            RecoveryEscalationDecision.WAITING_EXTERNAL,
        )
        self.assertIsNone(result.next_level)

    def test_existing_user_wait_is_preserved(self) -> None:
        result = self.service.decide(
            level=RecoveryEscalationLevel.LEVEL_2,
            task_id="task-1",
            workflow_id="workflow-1",
            run_id="run-1",
            recoverable=True,
            retry_exhausted=True,
            reason="user approval is required",
            waiting_for_user=True,
        )
        self.assertEqual(
            result.decision,
            RecoveryEscalationDecision.WAITING_FOR_USER,
        )

    def test_original_execution_identity_is_preserved(self) -> None:
        result = self.service.decide(
            level=RecoveryEscalationLevel.LEVEL_1,
            task_id="original-task",
            workflow_id="original-workflow",
            run_id="original-run",
            recoverable=True,
            retry_exhausted=True,
            reason="retry limit reached",
        )
        self.assertEqual(result.task_id, "original-task")
        self.assertEqual(result.workflow_id, "original-workflow")
        self.assertEqual(result.run_id, "original-run")

    def test_invalid_level_is_rejected(self) -> None:
        with self.assertRaises(TypeError):
            self.service.decide(
                level="LEVEL_1",
                task_id="task-1",
                workflow_id=None,
                run_id=None,
                recoverable=True,
                retry_exhausted=False,
                reason="invalid level",
            )

    def test_empty_task_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.service.decide(
                level=RecoveryEscalationLevel.LEVEL_1,
                task_id="",
                workflow_id=None,
                run_id=None,
                recoverable=True,
                retry_exhausted=False,
                reason="invalid task",
            )

    def test_empty_reason_is_rejected(self) -> None:
        with self.assertRaises(ValueError):
            self.service.decide(
                level=RecoveryEscalationLevel.LEVEL_1,
                task_id="task-1",
                workflow_id=None,
                run_id=None,
                recoverable=True,
                retry_exhausted=False,
                reason="",
            )


if __name__ == "__main__":
    unittest.main()
