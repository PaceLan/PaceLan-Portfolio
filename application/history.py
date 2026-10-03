from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class AgentHistoryStatus(str, Enum):
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"
    CANCELLED = "cancelled"


@dataclass(frozen=True)
class AgentHistoryEntry:
    history_id: str
    project_id: str
    task_id: str
    execution_id: str
    verification_status: str
    result_status: AgentHistoryStatus
    timestamp: str

    def __post_init__(self) -> None:
        for name in (
            "history_id", "project_id", "task_id",
            "execution_id", "verification_status", "timestamp"
        ):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be a non-empty string")

        if not isinstance(self.result_status, AgentHistoryStatus):
            raise TypeError("result_status must be an AgentHistoryStatus")

        try:
            datetime.fromisoformat(self.timestamp.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(
                "timestamp must be a valid ISO-8601 timestamp"
            ) from exc

    @classmethod
    def create(
        cls,
        *,
        history_id: str,
        project_id: str,
        task_id: str,
        execution_id: str,
        verification_status: str,
        result_status: AgentHistoryStatus,
        timestamp: str | None = None,
    ) -> "AgentHistoryEntry":
        return cls(
            history_id=history_id,
            project_id=project_id,
            task_id=task_id,
            execution_id=execution_id,
            verification_status=verification_status,
            result_status=result_status,
            timestamp=timestamp or datetime.now(timezone.utc).isoformat(),
        )


class AgentHistoryStore:
    def __init__(self) -> None:
        self._entries: list[AgentHistoryEntry] = []

    def append(self, entry: AgentHistoryEntry) -> AgentHistoryEntry:
        if not isinstance(entry, AgentHistoryEntry):
            raise TypeError("entry must be an AgentHistoryEntry")

        if any(e.history_id == entry.history_id for e in self._entries):
            raise ValueError(
                f"history_id is already registered: {entry.history_id}"
            )

        self._entries.append(entry)
        return entry

    def get(self, history_id: str) -> AgentHistoryEntry:
        for entry in self._entries:
            if entry.history_id == history_id:
                return entry
        raise KeyError(f"Unknown history_id: {history_id}")

    def list_all(self) -> tuple[AgentHistoryEntry, ...]:
        return tuple(self._entries)

    def list_for_task(self, task_id: str) -> tuple[AgentHistoryEntry, ...]:
        return tuple(e for e in self._entries if e.task_id == task_id)

    def list_for_project(
        self, project_id: str
    ) -> tuple[AgentHistoryEntry, ...]:
        return tuple(e for e in self._entries if e.project_id == project_id)

    def list_for_execution(
        self, execution_id: str
    ) -> tuple[AgentHistoryEntry, ...]:
        return tuple(e for e in self._entries if e.execution_id == execution_id)


__all__ = [
    "AgentHistoryEntry",
    "AgentHistoryStatus",
    "AgentHistoryStore",
]
