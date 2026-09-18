import tempfile
import unittest
from pathlib import Path

from snapshots.snapshot_core import SnapshotStore
from snapshots.snapshot_service import SnapshotService


class SnapshotServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        root = Path(self.temporary_directory.name)
        self.project_root = root / "project"
        self.snapshot_root = root / "snapshot-storage"
        self.project_root.mkdir()
        (self.project_root / "main.py").write_text("print('baseline')\n", encoding="utf-8")
        self.store = SnapshotStore(self.project_root, self.snapshot_root)
        self.service = SnapshotService(self.project_root, store=self.store)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_service_exposes_explicit_snapshot_lifecycle(self) -> None:
        created = self.service.create_snapshot()

        self.assertEqual(self.service.inspect_snapshot(created.snapshot_id), created)
        self.assertEqual(self.service.list_snapshots(), [created])

    def test_service_restores_with_explicit_overwrite_only(self) -> None:
        created = self.service.create_snapshot()
        target = self.project_root / "main.py"
        target.write_text("changed\n", encoding="utf-8")

        with self.assertRaises(FileExistsError):
            self.service.restore_snapshot(created.snapshot_id)
        self.assertEqual(target.read_text(encoding="utf-8"), "changed\n")

        self.service.restore_snapshot(created.snapshot_id, overwrite=True)
        self.assertEqual(target.read_text(encoding="utf-8"), "print('baseline')\n")

    def test_service_rejects_store_for_a_different_project_root(self) -> None:
        other_root = self.project_root.parent / "other-project"
        other_root.mkdir()
        other_store = SnapshotStore(other_root, self.project_root.parent / "other-snapshots")

        with self.assertRaises(ValueError):
            SnapshotService(self.project_root, store=other_store)

    def test_service_preserves_snapshot_boundary_validation(self) -> None:
        created = self.service.create_snapshot()
        metadata_path = self.snapshot_root / created.snapshot_id / "metadata.json"
        metadata_path.write_text(
            metadata_path.read_text(encoding="utf-8").replace('"main.py"', '"../outside.py"'),
            encoding="utf-8",
        )

        with self.assertRaises(ValueError):
            self.service.restore_snapshot(created.snapshot_id)

    def test_service_does_not_depend_on_history(self) -> None:
        created = self.service.create_snapshot()

        self.assertEqual(created.file_count, 1)
        self.assertFalse((self.snapshot_root / "history.json").exists())


if __name__ == "__main__":
    unittest.main()
