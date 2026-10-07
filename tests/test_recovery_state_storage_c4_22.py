import tempfile
import unittest
from pathlib import Path

from application.recovery_state_storage import (
    RecoveryState,
    RecoveryStateStorage,
)


class TestRecoveryStateStorageC422(unittest.TestCase):
    def make_state(self, sequence=1):
        return RecoveryState(
            recovery_id="recovery-1",
            snapshot_id="snapshot-1",
            status="PENDING",
            reason="process_crashed",
            sequence=sequence,
        )

    def test_save_and_load_survives_new_storage_instance(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = RecoveryStateStorage(directory)
            state = self.make_state()

            storage.save(state)
            restored = RecoveryStateStorage(directory).load()

            self.assertEqual(restored, state)

    def test_missing_state_returns_none(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertIsNone(RecoveryStateStorage(directory).load())

    def test_stale_state_cannot_replace_newer_state(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = RecoveryStateStorage(directory)
            storage.save(self.make_state(sequence=2))

            with self.assertRaises(ValueError):
                storage.save(self.make_state(sequence=1))

            self.assertEqual(storage.load().sequence, 2)

    def test_unsupported_schema_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            storage = RecoveryStateStorage(directory)
            path = storage.storage_path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                '{"schema_version": 999, "state": {}}',
                encoding="utf-8",
            )

            with self.assertRaises(ValueError):
                storage.load()

    def test_invalid_state_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(TypeError):
                RecoveryStateStorage(directory).save(object())


if __name__ == "__main__":
    unittest.main()
