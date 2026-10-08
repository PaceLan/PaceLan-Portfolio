import unittest
from datetime import datetime, timedelta, timezone

from application.chatgpt_global_analysis_recovery import (
    ChatGPTGlobalAnalysisRecoveryService,
    GlobalAnalysisRecoveryState,
)
from application.chatgpt_interruption import (
    ChatGPTInterruption,
    ChatGPTInterruptionType,
)


class ChatGPTGlobalAnalysisRecoveryC512Tests(unittest.TestCase):
    def setUp(self):
        self.service = ChatGPTGlobalAnalysisRecoveryService()
        self.interruption = ChatGPTInterruption(
            ChatGPTInterruptionType.GLOBAL_ANALYSIS_LIMIT
        )
        self.detected_at = datetime(
            2026, 10, 8, 1, 0, tzinfo=timezone.utc
        )

    def test_global_limit_enters_timed_recovery(self):
        result = self.service.prepare(
            self.interruption,
            task_id="task-1",
            detected_at=self.detected_at,
        )

        self.assertEqual(
            result.state,
            GlobalAnalysisRecoveryState.WAITING_FOR_RECOVERY,
        )
        self.assertEqual(
            result.waiting_until,
            self.detected_at + timedelta(minutes=15),
        )

    def test_original_task_identity_is_preserved(self):
        result = self.service.prepare(
            self.interruption,
            task_id="task-original",
            workflow_id="workflow-original",
            project_id="project-original",
            detected_at=self.detected_at,
        )

        self.assertEqual(result.task_id, "task-original")
        self.assertEqual(result.workflow_id, "workflow-original")
        self.assertEqual(result.project_id, "project-original")

    def test_single_conversation_limit_is_rejected(self):
        interruption = ChatGPTInterruption(
            ChatGPTInterruptionType.SINGLE_CONVERSATION_LIMIT
        )

        with self.assertRaises(ValueError):
            self.service.prepare(
                interruption,
                task_id="task-1",
                detected_at=self.detected_at,
            )

    def test_quick_check_limit_is_rejected(self):
        interruption = ChatGPTInterruption(
            ChatGPTInterruptionType.QUICK_CHECK_LIMIT
        )

        with self.assertRaises(ValueError):
            self.service.prepare(
                interruption,
                task_id="task-1",
                detected_at=self.detected_at,
            )

    def test_naive_detection_time_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.prepare(
                self.interruption,
                task_id="task-1",
                detected_at=datetime(2026, 10, 8, 1, 0),
            )


if __name__ == "__main__":
    unittest.main()
