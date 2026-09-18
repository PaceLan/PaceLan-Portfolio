import json
import tempfile
import unittest
from pathlib import Path

from history.history_core import HistoryEntry, HistoryStore


class HistoryCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.history_directory = Path(self.temporary_directory.name)
        self.store = HistoryStore(self.history_directory)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_history_entry_creation(self) -> None:
        entry = HistoryEntry(
            timestamp="2026-09-14T12:00:00Z",
            operation="read",
            target="core/main.py",
            result="completed",
            success=True,
        )

        self.assertEqual(entry.operation, "read")
        self.assertTrue(entry.success)

    def test_history_entry_serialization(self) -> None:
        entry = HistoryEntry("2026-09-14T12:00:00Z", "write", "notes.txt", "created", True)

        self.assertEqual(
            entry.to_dict(),
            {
                "timestamp": "2026-09-14T12:00:00Z",
                "operation": "write",
                "target": "notes.txt",
                "result": "created",
                "success": True,
            },
        )
        json.dumps(entry.to_dict())

    def test_history_entry_deserialization(self) -> None:
        entry = HistoryEntry("2026-09-14T12:00:00Z", "run", "main.py", "passed", True)

        self.assertEqual(HistoryEntry.from_dict(entry.to_dict()), entry)

    def test_append_one_history_entry(self) -> None:
        entry = HistoryEntry("2026-09-14T12:00:00Z", "read", "main.py", "completed", True)

        self.store.append(entry)

        self.assertEqual(self.store.read_history(), [entry])

    def test_append_multiple_entries_preserves_order(self) -> None:
        entries = [
            HistoryEntry("2026-09-14T12:00:00Z", "read", "one.py", "completed", True),
            HistoryEntry("2026-09-14T12:01:00Z", "run", "two.py", "passed", True),
            HistoryEntry("2026-09-14T12:02:00Z", "write", "three.txt", "failed", False),
        ]

        for entry in entries:
            self.store.append(entry)

        self.assertEqual(self.store.read_history(), entries)

    def test_read_history_from_disk(self) -> None:
        entry = HistoryEntry("2026-09-14T12:00:00Z", "read", "main.py", "completed", True)
        self.store.history_path.write_text(
            json.dumps([entry.to_dict()]),
            encoding="utf-8",
        )

        self.assertEqual(self.store.read_history(), [entry])

    def test_missing_history_file_returns_empty_history(self) -> None:
        self.assertFalse(self.store.history_path.exists())
        self.assertEqual(self.store.read_history(), [])

    def test_corrupt_json_raises_explicit_error(self) -> None:
        self.store.history_path.write_text("{not valid json", encoding="utf-8")

        with self.assertRaisesRegex(ValueError, "invalid JSON"):
            self.store.read_history()

    def test_persisted_history_contains_only_allowed_metadata(self) -> None:
        entry = HistoryEntry(
            "2026-09-14T12:00:00Z",
            "read",
            "src/main.py",
            "completed",
            True,
        )

        self.store.append(entry)
        persisted_text = self.store.history_path.read_text(encoding="utf-8")
        persisted_data = json.loads(persisted_text)

        self.assertEqual(set(persisted_data[0]), {
            "timestamp",
            "operation",
            "target",
            "result",
            "success",
        })
        self.assertNotIn("file_contents", persisted_text)
        self.assertNotIn("password", persisted_text)
        self.assertNotIn("api_key", persisted_text)
        self.assertNotIn("command_output", persisted_text)
        self.assertNotIn("environment", persisted_text)


if __name__ == "__main__":
    unittest.main()
