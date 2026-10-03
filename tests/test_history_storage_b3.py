from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from application.history import AgentHistoryEntry, AgentHistoryStatus
from application.history_storage import AgentHistoryStorage


class AgentHistoryStorageB3Tests(unittest.TestCase):
    def _entry(
        self,
        history_id: str = "history-1",
        task_id: str = "task-1",
    ) -> AgentHistoryEntry:
        return AgentHistoryEntry.create(
            history_id=history_id,
            project_id="project-1",
            task_id=task_id,
            execution_id=f"run-{history_id}",
            verification_status="verified",
            result_status=AgentHistoryStatus.COMPLETED,
            timestamp="2026-10-04T00:00:00+00:00",
        )

    def test_save_and_load_survive_restart(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            storage = AgentHistoryStorage()
            entries = (
                self._entry("history-1"),
                self._entry("history-2", "task-2"),
            )

            saved = storage.save(entries, project)

            self.assertTrue(saved.is_file())
            self.assertEqual(storage.load(project), entries)

            restarted_storage = AgentHistoryStorage()
            self.assertEqual(restarted_storage.load(project), entries)

    def test_missing_storage_returns_empty_history(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(
                AgentHistoryStorage().load(Path(directory)),
                (),
            )

    def test_corrupt_storage_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            target = (
                project
                / AgentHistoryStorage.DIRECTORY_NAME
                / AgentHistoryStorage.FILE_NAME
            )
            target.parent.mkdir(parents=True)
            target.write_text("{not valid json", encoding="utf-8")

            with self.assertRaises(ValueError):
                AgentHistoryStorage().load(project)

    def test_unsupported_schema_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            target = (
                project
                / AgentHistoryStorage.DIRECTORY_NAME
                / AgentHistoryStorage.FILE_NAME
            )
            target.parent.mkdir(parents=True)
            target.write_text(
                json.dumps({"schema_version": 999, "entries": []}),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                AgentHistoryStorage().load(project)

    def test_persisted_entries_contain_only_history_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            project = Path(directory)
            storage = AgentHistoryStorage()
            storage.save((self._entry(),), project)

            target = (
                project
                / AgentHistoryStorage.DIRECTORY_NAME
                / AgentHistoryStorage.FILE_NAME
            )
            payload = json.loads(target.read_text(encoding="utf-8"))

            self.assertEqual(
                set(payload["entries"][0]),
                {
                    "history_id",
                    "project_id",
                    "task_id",
                    "execution_id",
                    "verification_status",
                    "result_status",
                    "timestamp",
                },
            )
            text = target.read_text(encoding="utf-8")
            self.assertNotIn("file_contents", text)
            self.assertNotIn("password", text)
            self.assertNotIn("api_key", text)
            self.assertNotIn("command_output", text)
            self.assertNotIn("environment", text)

    def test_type_validation(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(TypeError):
                AgentHistoryStorage().save(
                    [object()],
                    Path(directory),
                )


if __name__ == "__main__":
    unittest.main()
