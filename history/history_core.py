"""Small local JSON history storage for Coding Assistant operations."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Union


_HISTORY_FIELDS = {"timestamp", "operation", "target", "result", "success"}


@dataclass(frozen=True)
class HistoryEntry:
    """A safe, metadata-only record of one completed operation."""

    timestamp: str
    operation: str
    target: str
    result: str
    success: bool

    def to_dict(self) -> Dict[str, object]:
        """Return the JSON-serializable representation of this entry."""
        return {
            "timestamp": self.timestamp,
            "operation": self.operation,
            "target": self.target,
            "result": self.result,
            "success": self.success,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "HistoryEntry":
        """Create an entry from a validated JSON object."""
        if not isinstance(data, dict):
            raise ValueError("History entry must be a JSON object")

        unexpected_fields = set(data) - _HISTORY_FIELDS
        missing_fields = _HISTORY_FIELDS - set(data)
        if unexpected_fields or missing_fields:
            raise ValueError("History entry has an invalid field set")
        if not all(isinstance(data[field], str) for field in _HISTORY_FIELDS - {"success"}):
            raise ValueError("History entry text fields must be strings")
        if not isinstance(data["success"], bool):
            raise ValueError("History entry success must be a boolean")

        return cls(
            timestamp=data["timestamp"],
            operation=data["operation"],
            target=data["target"],
            result=data["result"],
            success=data["success"],
        )


class HistoryStore:
    """Persist metadata-only history in ``history.json`` within a directory."""

    def __init__(self, history_directory: Union[str, Path]) -> None:
        self.history_directory = Path(history_directory).resolve()
        self.history_path = self.history_directory / "history.json"

    def append(self, entry: HistoryEntry) -> None:
        """Append ``entry`` while preserving all existing entries."""
        entries = self.read_history()
        entries.append(entry)
        serialized = [history_entry.to_dict() for history_entry in entries]
        self.history_path.write_text(
            json.dumps(serialized, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def read_history(self) -> List[HistoryEntry]:
        """Read all stored entries, treating a missing file as empty history.

        Raises:
            ValueError: If the history file is corrupt or has an invalid shape.
            IsADirectoryError: If ``history.json`` is a directory.
        """
        if not self.history_path.exists():
            return []
        if self.history_path.is_dir():
            raise IsADirectoryError(f"History path is a directory: {self.history_path}")

        try:
            raw_history = json.loads(self.history_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError("History file contains invalid JSON") from error

        if not isinstance(raw_history, list):
            raise ValueError("History file must contain a JSON list")

        return [HistoryEntry.from_dict(item) for item in raw_history]
