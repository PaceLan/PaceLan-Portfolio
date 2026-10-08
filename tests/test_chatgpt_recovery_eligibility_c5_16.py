import unittest
from datetime import datetime, timedelta, timezone

from application.chatgpt_interruption import ChatGPTInterruptionType
from application.chatgpt_recovery_eligibility import (
    ChatGPTRecoveryEligibilityDetector,
    RecoveryEligibility,
)
from application.chatgpt_timed_recovery_scheduler import (
    ChatGPTTimedRecoveryScheduler,
)


class ChatGPTRecoveryEligibilityC516Tests(unittest.TestCase):
    def setUp(self):
        self.detector = ChatGPTRecoveryEligibilityDetector()
        self.now = datetime(2026, 10, 8, 1, 0, tzinfo=timezone.utc)
        self.schedule = ChatGPTTimedRecoveryScheduler().schedule(
            detected_at=self.now
        )

    def test_single_conversation_limit_is_immediate(self):
        result = self.detector.detect(
            interruption_type=ChatGPTInterruptionType.SINGLE_CONVERSATION_LIMIT,
            task_id="task-1",
            workflow_id="workflow-1",
            recoverable=True,
            now=self.now,
        )
        self.assertEqual(
            result.eligibility,
            RecoveryEligibility.IMMEDIATE_RECOVERY,
        )

    def test_timed_recovery_before_due_is_delayed(self):
        result = self.detector.detect(
            interruption_type=ChatGPTInterruptionType.GLOBAL_ANALYSIS_LIMIT,
            task_id="task-1",
            workflow_id="workflow-1",
            recoverable=True,
            now=self.now + timedelta(minutes=10),
            schedule=self.schedule,
        )
        self.assertEqual(
            result.eligibility,
            RecoveryEligibility.DELAYED_RECOVERY,
        )

    def test_timed_recovery_when_due_is_immediate(self):
        result = self.detector.detect(
            interruption_type=ChatGPTInterruptionType.GLOBAL_ANALYSIS_LIMIT,
            task_id="task-1",
            workflow_id="workflow-1",
            recoverable=True,
            now=self.schedule.next_check,
            schedule=self.schedule,
        )
        self.assertEqual(
            result.eligibility,
            RecoveryEligibility.IMMEDIATE_RECOVERY,
        )

    def test_quick_check_uses_same_timed_rule(self):
        result = self.detector.detect(
            interruption_type=ChatGPTInterruptionType.QUICK_CHECK_LIMIT,
            task_id="task-1",
            workflow_id="workflow-1",
            recoverable=True,
            now=self.now + timedelta(minutes=10),
            schedule=self.schedule,
        )
        self.assertEqual(
            result.eligibility,
            RecoveryEligibility.DELAYED_RECOVERY,
        )

    def test_waiting_external_has_priority(self):
        result = self.detector.detect(
            interruption_type=ChatGPTInterruptionType.GLOBAL_ANALYSIS_LIMIT,
            task_id="task-1",
            workflow_id="workflow-1",
            recoverable=True,
            now=self.now,
            schedule=self.schedule,
            waiting_external=True,
        )
        self.assertEqual(
            result.eligibility,
            RecoveryEligibility.WAITING_EXTERNAL,
        )

    def test_waiting_for_user_has_priority(self):
        result = self.detector.detect(
            interruption_type=ChatGPTInterruptionType.GLOBAL_ANALYSIS_LIMIT,
            task_id="task-1",
            workflow_id="workflow-1",
            recoverable=True,
            now=self.now,
            schedule=self.schedule,
            waiting_for_user=True,
        )
        self.assertEqual(
            result.eligibility,
            RecoveryEligibility.WAITING_FOR_USER,
        )

    def test_nonrecoverable_is_not_recoverable(self):
        result = self.detector.detect(
            interruption_type=ChatGPTInterruptionType.QUICK_CHECK_LIMIT,
            task_id="task-1",
            workflow_id="workflow-1",
            recoverable=False,
            now=self.now,
            schedule=self.schedule,
        )
        self.assertEqual(
            result.eligibility,
            RecoveryEligibility.NOT_RECOVERABLE,
        )

    def test_timed_recovery_requires_schedule(self):
        with self.assertRaises(ValueError):
            self.detector.detect(
                interruption_type=ChatGPTInterruptionType.GLOBAL_ANALYSIS_LIMIT,
                task_id="task-1",
                workflow_id="workflow-1",
                recoverable=True,
                now=self.now,
            )

    def test_naive_now_is_rejected(self):
        with self.assertRaises(ValueError):
            self.detector.detect(
                interruption_type=ChatGPTInterruptionType.SINGLE_CONVERSATION_LIMIT,
                task_id="task-1",
                workflow_id="workflow-1",
                recoverable=True,
                now=datetime(2026, 10, 8, 1, 0),
            )


if __name__ == "__main__":
    unittest.main()
