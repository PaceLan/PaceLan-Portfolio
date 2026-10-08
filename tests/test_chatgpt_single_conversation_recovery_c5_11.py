import unittest

from application.chatgpt_interruption import (
    ChatGPTInterruption,
    ChatGPTInterruptionType,
)
from application.chatgpt_single_conversation_recovery import (
    ChatGPTSingleConversationRecoveryService,
    SingleConversationRecoveryState,
)


class ChatGPTSingleConversationRecoveryC511Tests(unittest.TestCase):
    def setUp(self):
        self.service = ChatGPTSingleConversationRecoveryService()
        self.interruption = ChatGPTInterruption(
            ChatGPTInterruptionType.SINGLE_CONVERSATION_LIMIT,
            "conversation limit reached",
        )

    def test_limit_requires_new_conversation(self):
        result = self.service.prepare(
            self.interruption,
            task_id="task-1",
            workflow_id="workflow-1",
            project_id="project-1",
        )

        self.assertEqual(
            result.state,
            SingleConversationRecoveryState.NEW_CONVERSATION_REQUIRED,
        )
        self.assertEqual(result.task_id, "task-1")
        self.assertEqual(result.workflow_id, "workflow-1")
        self.assertEqual(result.project_id, "project-1")

    def test_original_task_identity_is_preserved(self):
        result = self.service.prepare(
            self.interruption,
            task_id="task-original",
            workflow_id="workflow-original",
            project_id="project-original",
        )
        resumed = self.service.mark_ready(result)

        self.assertEqual(
            resumed.state,
            SingleConversationRecoveryState.READY_TO_RESUME,
        )
        self.assertEqual(resumed.task_id, "task-original")
        self.assertEqual(resumed.workflow_id, "workflow-original")
        self.assertEqual(resumed.project_id, "project-original")

    def test_other_interruption_types_are_rejected(self):
        interruption = ChatGPTInterruption(
            ChatGPTInterruptionType.GLOBAL_ANALYSIS_LIMIT
        )

        with self.assertRaises(ValueError):
            self.service.prepare(interruption, task_id="task-1")

    def test_missing_task_id_is_rejected(self):
        with self.assertRaises(ValueError):
            self.service.prepare(self.interruption, task_id="")

    def test_invalid_interruption_is_rejected(self):
        with self.assertRaises(TypeError):
            self.service.prepare(
                "SINGLE_CONVERSATION_LIMIT",
                task_id="task-1",
            )


if __name__ == "__main__":
    unittest.main()
