"""Lightweight, local project snapshots for Coding Assistant."""

import json
import shutil
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Union


_METADATA_FIELDS = {"snapshot_id", "timestamp", "file_count", "files"}
_IGNORED_DIRECTORIES = {".git", ".venv", "__pycache__", "snapshots"}


@dataclass(frozen=True)
class SnapshotMetadata:
    """Metadata describing one recoverable project snapshot."""

    snapshot_id: str
    timestamp: str
    file_count: int
    files: List[str]

    def to_dict(self) -> Dict[str, object]:
        """Return the JSON-serializable metadata representation."""
        return {
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "file_count": self.file_count,
            "files": self.files,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SnapshotMetadata":
        """Create metadata from a validated JSON object."""
        if not isinstance(data, dict):
            raise ValueError("Snapshot metadata must be a JSON object")
        if set(data) != _METADATA_FIELDS:
            raise ValueError("Snapshot metadata has an invalid field set")
        if not isinstance(data["snapshot_id"], str) or not data["snapshot_id"]:
            raise ValueError("Snapshot ID must be a non-empty string")
        if not isinstance(data["timestamp"], str):
            raise ValueError("Snapshot timestamp must be a string")
        if not isinstance(data["file_count"], int) or data["file_count"] < 0:
            raise ValueError("Snapshot file count must be a non-negative integer")
        if not isinstance(data["files"], list) or not all(
            isinstance(path, str) for path in data["files"]
        ):
            raise ValueError("Snapshot files must be a list of strings")
        if data["file_count"] != len(data["files"]):
            raise ValueError("Snapshot file count does not match file list")

        return cls(
            snapshot_id=data["snapshot_id"],
            timestamp=data["timestamp"],
            file_count=data["file_count"],
            files=list(data["files"]),
        )


class SnapshotStore:
    """Create, inspect, list, and safely restore local project snapshots."""

    def __init__(
        self,
        project_root: Union[str, Path],
        snapshot_directory: Union[str, Path],
    ) -> None:
        self.project_root = Path(project_root).resolve()
        self.snapshot_directory = Path(snapshot_directory).resolve()
        if not self.project_root.is_dir():
            raise NotADirectoryError(f"Project root is not a directory: {self.project_root}")
        self.snapshot_directory.mkdir(parents=True, exist_ok=True)

    def create_snapshot(self) -> SnapshotMetadata:
        """Create and return a read-only copy of the current project state."""
        snapshot_id = uuid.uuid4().hex
        snapshot_path = self.snapshot_directory / snapshot_id
        files_path = snapshot_path / "files"
        files_path.mkdir(parents=True)

        files: List[str] = []
        try:
            for source_path in self._project_files():
                relative_path = source_path.relative_to(self.project_root)
                target_path = files_path / relative_path
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)
                files.append(relative_path.as_posix())

            metadata = SnapshotMetadata(
                snapshot_id=snapshot_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                file_count=len(files),
                files=files,
            )
            (snapshot_path / "metadata.json").write_text(
                json.dumps(metadata.to_dict(), ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return metadata
        except Exception:
            shutil.rmtree(snapshot_path, ignore_errors=True)
            raise

    def list_snapshots(self) -> List[SnapshotMetadata]:
        """Return valid snapshots in deterministic ID order."""
        snapshots = []
        for snapshot_path in sorted(self.snapshot_directory.iterdir(), key=lambda path: path.name):
            if snapshot_path.is_dir() and (snapshot_path / "metadata.json").is_file():
                snapshots.append(self.inspect_snapshot(snapshot_path.name))
        return snapshots

    def inspect_snapshot(self, snapshot_id: str) -> SnapshotMetadata:
        """Return metadata for one snapshot ID."""
        snapshot_path = self._snapshot_path(snapshot_id)
        metadata_path = snapshot_path / "metadata.json"
        if not metadata_path.is_file():
            raise FileNotFoundError(f"Snapshot metadata does not exist: {snapshot_id}")
        try:
            data = json.loads(metadata_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("Snapshot metadata contains invalid JSON") from error
        metadata = SnapshotMetadata.from_dict(data)
        if metadata.snapshot_id != snapshot_id:
            raise ValueError("Snapshot metadata ID does not match its path")
        return metadata

    def restore_snapshot(self, snapshot_id: str, overwrite: bool = False) -> SnapshotMetadata:
        """Restore snapshot files into the project root.

        Existing project files are refused unless ``overwrite`` is explicitly
        set to ``True``. Unrelated project files are never deleted.
        """
        metadata = self.inspect_snapshot(snapshot_id)
        snapshot_files = self._snapshot_path(snapshot_id) / "files"
        source_paths = []
        target_paths = []
        for relative_name in metadata.files:
            relative_path = self._safe_relative_path(relative_name)
            source_path = (snapshot_files / relative_path).resolve()
            if not source_path.is_relative_to(snapshot_files.resolve()):
                raise ValueError("Snapshot file escapes snapshot storage")
            if not source_path.is_file():
                raise FileNotFoundError(f"Snapshot file does not exist: {relative_name}")
            target_path = (self.project_root / relative_path).resolve()
            if not target_path.is_relative_to(self.project_root):
                raise ValueError("Snapshot restore path escapes project root")
            source_paths.append(source_path)
            target_paths.append(target_path)

        if not overwrite:
            conflicts = [path for path in target_paths if path.exists()]
            if conflicts:
                raise FileExistsError(f"Snapshot restore would overwrite: {conflicts[0]}")

        for source_path, target_path in zip(source_paths, target_paths):
            target_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source_path, target_path)
        return metadata

    def _project_files(self) -> List[Path]:
        files = []
        for path in self.project_root.rglob("*"):
            if self.snapshot_directory.is_relative_to(self.project_root) and path.is_relative_to(
                self.snapshot_directory
            ):
                continue
            if any(part in _IGNORED_DIRECTORIES for part in path.relative_to(self.project_root).parts):
                continue
            if path.is_file():
                files.append(path)
        return sorted(files, key=lambda path: path.relative_to(self.project_root).as_posix())

    def _snapshot_path(self, snapshot_id: str) -> Path:
        if not snapshot_id or Path(snapshot_id).name != snapshot_id:
            raise ValueError("Invalid snapshot ID")
        snapshot_path = (self.snapshot_directory / snapshot_id).resolve()
        if not snapshot_path.is_relative_to(self.snapshot_directory):
            raise ValueError("Snapshot path escapes snapshot storage")
        if not snapshot_path.is_dir():
            raise FileNotFoundError(f"Snapshot does not exist: {snapshot_id}")
        return snapshot_path

    @staticmethod
    def _safe_relative_path(relative_name: str) -> Path:
        relative_path = Path(relative_name)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError("Snapshot contains an unsafe relative path")
        return relative_path
