import unittest

from application.history import (
    AgentHistoryEntry,
    AgentHistoryStatus,
    AgentHistoryStore,
)


class TestAgentHistoryA6(unittest.TestCase):
    def _entry(
        self,
        history_id="history-1",
        project_id="project-1",
        task_id="task-1",
        execution_id="execution-1",
        verification_status="verified",
        result_status=AgentHistoryStatus.COMPLETED,
        timestamp="2026-10-03T00:00:00+00:00",
    ):
        return AgentHistoryEntry(
            history_id=history_id,
            project_id=project_id,
            task_id=task_id,
            execution_id=execution_id,
            verification_status=verification_status,
            result_status=result_status,
            timestamp=timestamp,
        )

    def test_entry_records_complete_agent_lifecycle(self):
        entry = self._entry()

        self.assertEqual(entry.project_id, "project-1")
        self.assertEqual(entry.task_id, "task-1")
        self.assertEqual(entry.execution_id, "execution-1")
        self.assertEqual(entry.verification_status, "verified")
        self.assertEqual(entry.result_status, AgentHistoryStatus.COMPLETED)

    def test_store_appends_and_preserves_order(self):
        store = AgentHistoryStore()
        first = self._entry(
            "history-1",
            timestamp="2026-10-03T00:00:00+00:00",
        )
        second = self._entry(
            "history-2",
            task_id="task-2",
            execution_id="execution-2",
            timestamp="2026-10-03T00:01:00+00:00",
        )

        store.append(first)
        store.append(second)

        self.assertEqual(store.list_all(), (first, second))

    def test_store_gets_entry_by_history_id(self):
        store = AgentHistoryStore()
        entry = self._entry()
        store.append(entry)

        self.assertIs(store.get("history-1"), entry)

    def test_store_queries_by_task(self):
        store = AgentHistoryStore()
        first = self._entry("history-1", task_id="task-1")
        second = self._entry("history-2", task_id="task-2")
        third = self._entry("history-3", task_id="task-1")

        for entry in (first, second, third):
            store.append(entry)

        self.assertEqual(
            store.list_for_task("task-1"),
            (first, third),
        )

    def test_store_queries_by_project(self):
        store = AgentHistoryStore()
        first = self._entry("history-1", project_id="project-1")
        second = self._entry("history-2", project_id="project-2")
        third = self._entry("history-3", project_id="project-1")

        for entry in (first, second, third):
            store.append(entry)

        self.assertEqual(
            store.list_for_project("project-1"),
            (first, third),
        )

    def test_store_queries_by_execution(self):
        store = AgentHistoryStore()
        first = self._entry("history-1", execution_id="execution-1")
        second = self._entry("history-2", execution_id="execution-2")
        third = self._entry("history-3", execution_id="execution-1")

        for entry in (first, second, third):
            store.append(entry)

        self.assertEqual(
            store.list_for_execution("execution-1"),
            (first, third),
        )

    def test_failed_history_is_recordable(self):
        entry = self._entry(
            verification_status="not_verified",
            result_status=AgentHistoryStatus.FAILED,
        )

        self.assertEqual(
            entry.result_status,
            AgentHistoryStatus.FAILED,
        )

    def test_blocked_history_is_recordable(self):
        entry = self._entry(
            verification_status="blocked",
            result_status=AgentHistoryStatus.BLOCKED,
        )

        self.assertEqual(
            entry.result_status,
            AgentHistoryStatus.BLOCKED,
        )

    def test_cancelled_history_is_recordable(self):
        entry = self._entry(
            verification_status="not_verified",
            result_status=AgentHistoryStatus.CANCELLED,
        )

        self.assertEqual(
            entry.result_status,
            AgentHistoryStatus.CANCELLED,
        )

    def test_duplicate_history_id_is_rejected(self):
        store = AgentHistoryStore()
        store.append(self._entry("history-1"))

        with self.assertRaisesRegex(ValueError, "already registered"):
            store.append(self._entry("history-1"))

    def test_invalid_entry_type_is_rejected(self):
        store = AgentHistoryStore()

        with self.assertRaises(TypeError):
            store.append("not-an-entry")

    def test_history_is_metadata_only(self):
        entry = self._entry()

        self.assertFalse(hasattr(entry, "file_contents"))
        self.assertFalse(hasattr(entry, "environment"))
        self.assertFalse(hasattr(entry, "api_key"))


if __name__ == "__main__":
    unittest.main()
