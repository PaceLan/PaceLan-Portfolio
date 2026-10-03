"""Durable storage for A6 Agent lifecycle history."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from .history import AgentHistoryEntry, AgentHistoryStatus


class AgentHistoryStorage:
    """Persist A6 AgentHistoryEntry records as local JSON."""

    SCHEMA_VERSION = 1
    DIRECTORY_NAME = ".pacepilot"
    FILE_NAME = "agent_history.json"

    def _storage_path(self, project_path: str | Path) -> Path:
        return Path(project_path).resolve() / self.DIRECTORY_NAME / self.FILE_NAME

    def exists(self, project_path: str | Path) -> bool:
        return self._storage_path(project_path).is_file()

    def save(
        self,
        entries: tuple[AgentHistoryEntry, ...] | list[AgentHistoryEntry],
        project_path: str | Path,
    ) -> Path:
        if not isinstance(entries, (tuple, list)):
            raise TypeError("entries must be a tuple or list of AgentHistoryEntry")

        for entry in entries:
            if not isinstance(entry, AgentHistoryEntry):
                raise TypeError("entries must contain only AgentHistoryEntry")

        root = Path(project_path).resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError("project_path must be an existing directory")

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "entries": [self._entry_to_dict(entry) for entry in entries],
        }

        target = self._storage_path(root)
        target.parent.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=".agent-history.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        try:
            os.replace(temporary, target)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

        return target

    def load(self, project_path: str | Path) -> tuple[AgentHistoryEntry, ...]:
        target = self._storage_path(project_path)

        if not target.is_file():
            return ()

        try:
            with target.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(f"Invalid agent history storage: {target}") from exc

        if not isinstance(payload, dict):
            raise ValueError("Agent history storage must contain an object")

        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported agent history storage schema: "
                f"{payload.get('schema_version')!r}"
            )

        raw_entries = payload.get("entries")
        if not isinstance(raw_entries, list):
            raise ValueError("Agent history entries must be a JSON list")

        try:
            return tuple(self._entry_from_dict(item) for item in raw_entries)
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("Invalid agent history storage structure") from exc

    @staticmethod
    def _entry_to_dict(entry: AgentHistoryEntry) -> dict[str, Any]:
        return {
            "history_id": entry.history_id,
            "project_id": entry.project_id,
            "task_id": entry.task_id,
            "execution_id": entry.execution_id,
            "verification_status": entry.verification_status,
            "result_status": entry.result_status.value,
            "timestamp": entry.timestamp,
        }

    @staticmethod
    def _entry_from_dict(data: dict[str, Any]) -> AgentHistoryEntry:
        if not isinstance(data, dict):
            raise ValueError("Agent history entry must be a JSON object")

        return AgentHistoryEntry(
            history_id=data["history_id"],
            project_id=data["project_id"],
            task_id=data["task_id"],
            execution_id=data["execution_id"],
            verification_status=data["verification_status"],
            result_status=AgentHistoryStatus(data["result_status"]),
            timestamp=data["timestamp"],
        )


__all__ = ["AgentHistoryStorage"]
