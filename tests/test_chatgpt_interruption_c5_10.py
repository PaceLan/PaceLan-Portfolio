import unittest

from application.chatgpt_interruption import (
    ChatGPTInterruption,
    ChatGPTInterruptionType,
)


class ChatGPTInterruptionC510Tests(unittest.TestCase):
    def test_single_conversation_limit_is_distinct(self):
        interruption = ChatGPTInterruption(
            ChatGPTInterruptionType.SINGLE_CONVERSATION_LIMIT
        )
        self.assertEqual(
            interruption.interruption_type,
            ChatGPTInterruptionType.SINGLE_CONVERSATION_LIMIT,
        )

    def test_global_analysis_limit_is_distinct(self):
        interruption = ChatGPTInterruption(
            ChatGPTInterruptionType.GLOBAL_ANALYSIS_LIMIT
        )
        self.assertNotEqual(
            interruption.interruption_type,
            ChatGPTInterruptionType.SINGLE_CONVERSATION_LIMIT,
        )

    def test_quick_check_limit_is_distinct(self):
        interruption = ChatGPTInterruption(
            ChatGPTInterruptionType.QUICK_CHECK_LIMIT
        )
        self.assertNotEqual(
            interruption.interruption_type,
            ChatGPTInterruptionType.GLOBAL_ANALYSIS_LIMIT,
        )

    def test_unknown_is_explicit(self):
        interruption = ChatGPTInterruption(
            ChatGPTInterruptionType.UNKNOWN,
            message="state cannot be verified",
        )
        self.assertEqual(
            interruption.interruption_type,
            ChatGPTInterruptionType.UNKNOWN,
        )
        self.assertEqual(interruption.message, "state cannot be verified")

    def test_invalid_type_is_rejected(self):
        with self.assertRaises(TypeError):
            ChatGPTInterruption("QUOTA_LIMIT")

    def test_types_are_not_generic_quota_limit(self):
        self.assertNotIn(
            "QUOTA_LIMIT",
            {item.value for item in ChatGPTInterruptionType},
        )


if __name__ == "__main__":
    unittest.main()
