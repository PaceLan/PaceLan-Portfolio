from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile


@dataclass(frozen=True)
class ChatGPTInterruptionPersistence:
    interruption_reason: str
    detected_at: datetime
    waiting_until: datetime | None
    next_check: datetime | None
    retry_count: int
    recovery_strategy: str
    recovery_state: str
    task_id: str
    workflow_id: str | None = None
    project_id: str | None = None

    def __post_init__(self) -> None:
        if not self.interruption_reason.strip():
            raise ValueError("interruption_reason must not be empty")
        if not self.recovery_strategy.strip():
            raise ValueError("recovery_strategy must not be empty")
        if not self.recovery_state.strip():
            raise ValueError("recovery_state must not be empty")
        if not self.task_id.strip():
            raise ValueError("task_id must not be empty")
        if self.detected_at.tzinfo is None:
            raise ValueError("detected_at must be timezone-aware")
        if self.waiting_until is not None and self.waiting_until.tzinfo is None:
            raise ValueError("waiting_until must be timezone-aware")
        if self.next_check is not None and self.next_check.tzinfo is None:
            raise ValueError("next_check must be timezone-aware")
        if self.retry_count < 0:
            raise ValueError("retry_count must not be negative")


class ChatGPTInterruptionPersistenceStorage:
    SCHEMA_VERSION = 1
    FILE_NAME = "chatgpt_interruption.json"

    def _path(self, project_path: str | Path) -> Path:
        root = Path(project_path)
        if not root.exists() or not root.is_dir():
            raise ValueError("project_path must be an existing directory")
        return root / ".pacepilot" / self.FILE_NAME

    def save(
        self,
        project_path: str | Path,
        state: ChatGPTInterruptionPersistence,
    ) -> Path:
        if not isinstance(state, ChatGPTInterruptionPersistence):
            raise TypeError(
                "state must be a ChatGPTInterruptionPersistence"
            )

        target = self._path(project_path)
        target.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "interruption_reason": state.interruption_reason,
            "detected_at": state.detected_at.isoformat(),
            "waiting_until": (
                state.waiting_until.isoformat()
                if state.waiting_until is not None
                else None
            ),
            "next_check": (
                state.next_check.isoformat()
                if state.next_check is not None
                else None
            ),
            "retry_count": state.retry_count,
            "recovery_strategy": state.recovery_strategy,
            "recovery_state": state.recovery_state,
            "task_id": state.task_id,
            "workflow_id": state.workflow_id,
            "project_id": state.project_id,
        }

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=".chatgpt-interruption.",
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

    def load(
        self,
        project_path: str | Path,
    ) -> ChatGPTInterruptionPersistence | None:
        target = self._path(project_path)

        if not target.is_file():
            return None

        try:
            with target.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Invalid ChatGPT interruption storage: {target}"
            ) from exc

        if not isinstance(payload, dict):
            raise ValueError(
                "ChatGPT interruption storage must contain an object"
            )

        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError(
                "Unsupported ChatGPT interruption storage schema"
            )

        try:
            return ChatGPTInterruptionPersistence(
                interruption_reason=payload["interruption_reason"],
                detected_at=datetime.fromisoformat(payload["detected_at"]),
                waiting_until=(
                    datetime.fromisoformat(payload["waiting_until"])
                    if payload["waiting_until"] is not None
                    else None
                ),
                next_check=(
                    datetime.fromisoformat(payload["next_check"])
                    if payload["next_check"] is not None
                    else None
                ),
                retry_count=payload["retry_count"],
                recovery_strategy=payload["recovery_strategy"],
                recovery_state=payload["recovery_state"],
                task_id=payload["task_id"],
                workflow_id=payload.get("workflow_id"),
                project_id=payload.get("project_id"),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid ChatGPT interruption storage structure"
            ) from exc


__all__ = [
    "ChatGPTInterruptionPersistence",
    "ChatGPTInterruptionPersistenceStorage",
]
