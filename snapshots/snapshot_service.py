"""Stable internal Snapshot Core API for future workflow integrations."""

from pathlib import Path
from typing import List, Optional, Union

from snapshots.snapshot_core import SnapshotMetadata, SnapshotStore


class SnapshotService:
    """Expose explicit snapshot operations for a managed project."""

    def __init__(
        self,
        project_root: Union[str, Path],
        store: Optional[SnapshotStore] = None,
        snapshot_directory: Optional[Union[str, Path]] = None,
    ) -> None:
        self.project_root = Path(project_root).resolve()
        if store is not None:
            if store.project_root != self.project_root:
                raise ValueError("Snapshot store project root does not match the service root")
            self.store = store
        else:
            storage_path = snapshot_directory or (self.project_root / "snapshots")
            self.store = SnapshotStore(self.project_root, storage_path)

    def create_snapshot(self) -> SnapshotMetadata:
        """Explicitly capture the current managed project state."""
        return self.store.create_snapshot()

    def list_snapshots(self) -> List[SnapshotMetadata]:
        """List available snapshots for the managed project."""
        return self.store.list_snapshots()

    def inspect_snapshot(self, snapshot_id: str) -> SnapshotMetadata:
        """Inspect one snapshot without changing project files."""
        return self.store.inspect_snapshot(snapshot_id)

    def restore_snapshot(self, snapshot_id: str, overwrite: bool = False) -> SnapshotMetadata:
        """Explicitly restore one snapshot using the store safety policy."""
        return self.store.restore_snapshot(snapshot_id, overwrite=overwrite)
