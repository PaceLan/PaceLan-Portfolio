import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from application.chatgpt_interruption_persistence import (
    ChatGPTInterruptionPersistence,
    ChatGPTInterruptionPersistenceStorage,
)


class ChatGPTInterruptionPersistenceC514Tests(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.storage = ChatGPTInterruptionPersistenceStorage()
        self.detected_at = datetime(
            2026, 10, 8, 1, 0, tzinfo=timezone.utc
        )
        self.state = ChatGPTInterruptionPersistence(
            interruption_reason="GLOBAL_ANALYSIS_LIMIT",
            detected_at=self.detected_at,
            waiting_until=self.detected_at + timedelta(minutes=15),
            next_check=self.detected_at + timedelta(minutes=18),
            retry_count=2,
            recovery_strategy="EXIT_AND_TIMED_RECOVERY",
            recovery_state="WAITING_FOR_RECOVERY",
            task_id="task-1",
            workflow_id="workflow-1",
            project_id="project-1",
        )

    def test_all_interruption_fields_survive_restart(self):
        self.storage.save(self.root, self.state)

        restored = self.storage.load(self.root)

        self.assertEqual(restored, self.state)

    def test_storage_uses_pacepilot_directory(self):
        path = self.storage.save(self.root, self.state)

        self.assertEqual(
            path,
            self.root / ".pacepilot" / "chatgpt_interruption.json",
        )
        self.assertTrue(path.is_file())

    def test_missing_state_returns_none(self):
        self.assertIsNone(self.storage.load(self.root))

    def test_negative_retry_count_is_rejected(self):
        with self.assertRaises(ValueError):
            ChatGPTInterruptionPersistence(
                interruption_reason="LIMIT",
                detected_at=self.detected_at,
                waiting_until=None,
                next_check=None,
                retry_count=-1,
                recovery_strategy="WAIT",
                recovery_state="WAITING",
                task_id="task-1",
            )

    def test_naive_timestamp_is_rejected(self):
        with self.assertRaises(ValueError):
            ChatGPTInterruptionPersistence(
                interruption_reason="LIMIT",
                detected_at=datetime(2026, 10, 8, 1, 0),
                waiting_until=None,
                next_check=None,
                retry_count=0,
                recovery_strategy="WAIT",
                recovery_state="WAITING",
                task_id="task-1",
            )


if __name__ == "__main__":
    unittest.main()
