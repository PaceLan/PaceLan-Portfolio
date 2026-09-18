import json
import tempfile
import unittest
from pathlib import Path

from snapshots.snapshot_core import SnapshotMetadata, SnapshotStore


class SnapshotCoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary_directory = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary_directory.name)
        self.project_root = self.root / "project"
        self.snapshot_root = self.root / "snapshots"
        self.project_root.mkdir()
        (self.project_root / "src").mkdir()
        (self.project_root / "src" / "main.py").write_text("print('original')\n", encoding="utf-8")
        (self.project_root / "README.md").write_text("readme\n", encoding="utf-8")
        self.store = SnapshotStore(self.project_root, self.snapshot_root)

    def tearDown(self) -> None:
        self.temporary_directory.cleanup()

    def test_create_snapshot_returns_metadata_and_copies_project_files(self) -> None:
        metadata = self.store.create_snapshot()

        self.assertIsInstance(metadata, SnapshotMetadata)
        self.assertEqual(metadata.file_count, 2)
        self.assertEqual(metadata.files, ["README.md", "src/main.py"])
        self.assertTrue((self.snapshot_root / metadata.snapshot_id / "metadata.json").is_file())

    def test_list_snapshots_returns_metadata(self) -> None:
        first = self.store.create_snapshot()
        second = self.store.create_snapshot()

        snapshots = self.store.list_snapshots()

        self.assertEqual([item.snapshot_id for item in snapshots], sorted([first.snapshot_id, second.snapshot_id]))

    def test_inspect_snapshot_returns_metadata(self) -> None:
        created = self.store.create_snapshot()

        inspected = self.store.inspect_snapshot(created.snapshot_id)

        self.assertEqual(inspected, created)

    def test_restore_snapshot_requires_explicit_overwrite(self) -> None:
        created = self.store.create_snapshot()
        target = self.project_root / "src" / "main.py"
        target.write_text("changed\n", encoding="utf-8")

        with self.assertRaises(FileExistsError):
            self.store.restore_snapshot(created.snapshot_id)
        self.assertEqual(target.read_text(encoding="utf-8"), "changed\n")

        self.store.restore_snapshot(created.snapshot_id, overwrite=True)
        self.assertEqual(target.read_text(encoding="utf-8"), "print('original')\n")

    def test_restore_snapshot_restores_missing_files_without_deleting_unrelated_files(self) -> None:
        created = self.store.create_snapshot()
        target = self.project_root / "README.md"
        target.unlink()
        unrelated = self.project_root / "unrelated.txt"
        unrelated.write_text("keep", encoding="utf-8")

        self.store.restore_snapshot(created.snapshot_id, overwrite=True)

        self.assertEqual(target.read_text(encoding="utf-8"), "readme\n")
        self.assertEqual(unrelated.read_text(encoding="utf-8"), "keep")

    def test_restore_rejects_unsafe_metadata_paths(self) -> None:
        created = self.store.create_snapshot()
        metadata_path = self.snapshot_root / created.snapshot_id / "metadata.json"
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        metadata["files"] = ["../outside.txt"]
        metadata["file_count"] = 1
        metadata_path.write_text(json.dumps(metadata), encoding="utf-8")

        with self.assertRaises(ValueError):
            self.store.restore_snapshot(created.snapshot_id)

    def test_missing_snapshot_is_reported(self) -> None:
        with self.assertRaises(FileNotFoundError):
            self.store.inspect_snapshot("missing")

    def test_snapshot_metadata_round_trip(self) -> None:
        metadata = SnapshotMetadata("abc", "2026-09-14T12:00:00Z", 1, ["main.py"])

        self.assertEqual(SnapshotMetadata.from_dict(metadata.to_dict()), metadata)

    def test_snapshot_creation_does_not_modify_project_files(self) -> None:
        before = {
            path.relative_to(self.project_root).as_posix(): path.read_bytes()
            for path in self.project_root.rglob("*")
            if path.is_file()
        }

        self.store.create_snapshot()

        after = {
            path.relative_to(self.project_root).as_posix(): path.read_bytes()
            for path in self.project_root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(after, before)


if __name__ == "__main__":
    unittest.main()
