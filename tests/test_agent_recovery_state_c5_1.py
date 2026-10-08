from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from application.agent_recovery_state import (
    AgentRecoveryPhase,
    AgentRecoveryState,
)
from application.agent_recovery_state_storage import (
    AgentRecoveryStateStorage,
)


class AgentRecoveryStateC51Tests(unittest.TestCase):
    def make_state(self, **overrides) -> AgentRecoveryState:
        data = {
            "recovery_id": "recovery-1",
            "project_id": "project-1",
            "task_id": "task-1",
            "workflow_id": "workflow-1",
            "run_id": "run-1",
            "session_id": "session-1",
            "phase": AgentRecoveryPhase.RECONNECTING,
            "task_status": "RUNNING",
            "connection_state": "RECOVERABLE",
            "recoverable": True,
            "retry_attempt": 2,
            "retry_limit": 5,
            "reason": "connection lost",
            "error": "connection interrupted",
            "updated_at": "2026-10-08T12:00:00+13:00",
            "sequence": 3,
        }
        data.update(overrides)
        return AgentRecoveryState(**data)

    def test_missing_state_returns_none(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = AgentRecoveryStateStorage(directory)
            self.assertFalse(storage.exists())
            self.assertIsNone(storage.load())

    def test_state_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = AgentRecoveryStateStorage(directory)
            state = self.make_state()

            storage.save(state)

            self.assertTrue(storage.exists())
            self.assertEqual(storage.load(), state)

    def test_state_survives_new_storage_instance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            state = self.make_state(sequence=7)

            AgentRecoveryStateStorage(directory).save(state)

            restored = AgentRecoveryStateStorage(Path(directory)).load()

            self.assertEqual(restored, state)

    def test_sequence_cannot_move_backwards(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = AgentRecoveryStateStorage(directory)
            current = self.make_state(sequence=5)
            older = self.make_state(sequence=4)

            storage.save(current)

            with self.assertRaises(ValueError):
                storage.save(older)

            self.assertEqual(storage.load(), current)

    def test_invalid_model_values_are_rejected(self) -> None:
        invalid_cases = (
            {"recovery_id": ""},
            {"project_id": ""},
            {"task_id": ""},
            {"workflow_id": ""},
            {"run_id": ""},
            {"session_id": ""},
            {"retry_attempt": -1},
            {"retry_limit": -1},
            {"sequence": -1},
        )

        for overrides in invalid_cases:
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValueError):
                    self.make_state(**overrides)

    def test_invalid_schema_version_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = AgentRecoveryStateStorage(directory)
            storage.save(self.make_state())

            path = storage.storage_path
            payload = json.loads(path.read_text(encoding="utf-8"))
            payload["schema_version"] = 999
            path.write_text(
                json.dumps(payload),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                storage.load()

    def test_invalid_state_structure_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            storage = AgentRecoveryStateStorage(directory)
            path = storage.storage_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                json.dumps(
                    {
                        "schema_version": storage.SCHEMA_VERSION,
                        "state": {"recovery_id": "only-one-field"},
                    }
                ),
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                storage.load()


if __name__ == "__main__":
    unittest.main()
