from __future__ import annotations

import json
import os
from dataclasses import asdict
from pathlib import Path
from tempfile import NamedTemporaryFile

from application.agent_recovery_state import (
    AgentRecoveryPhase,
    AgentRecoveryState,
)


class AgentRecoveryStateStorage:
    """Durable storage for external Agent recovery state."""

    SCHEMA_VERSION = 1
    DIRECTORY_NAME = ".pacepilot"
    FILE_NAME = "agent_recovery_state.json"

    def __init__(self, project_path: str | Path) -> None:
        self._project_path = Path(project_path)

    @property
    def storage_path(self) -> Path:
        return (
            self._project_path
            / self.DIRECTORY_NAME
            / self.FILE_NAME
        )

    def save(self, state: AgentRecoveryState) -> None:
        if not isinstance(state, AgentRecoveryState):
            raise TypeError("state must be an AgentRecoveryState")

        current = self.load()
        if current is not None and state.sequence < current.sequence:
            raise ValueError("recovery state sequence cannot move backwards")

        target = self.storage_path
        target.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "state": {
                **asdict(state),
                "phase": state.phase.value,
            },
        }

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=".agent-recovery.",
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

    def exists(self) -> bool:
        return self.storage_path.is_file()

    def load(self) -> AgentRecoveryState | None:
        target = self.storage_path
        if not target.is_file():
            return None

        try:
            with target.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Invalid Agent recovery state: {target}"
            ) from exc

        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError(
                "Unsupported Agent recovery state schema: "
                f"{payload.get('schema_version')!r}"
            )

        data = payload.get("state")
        if not isinstance(data, dict):
            raise ValueError("Invalid Agent recovery state structure")

        try:
            return AgentRecoveryState(
                recovery_id=data["recovery_id"],
                project_id=data["project_id"],
                task_id=data["task_id"],
                workflow_id=data.get("workflow_id"),
                run_id=data.get("run_id"),
                session_id=data.get("session_id"),
                phase=AgentRecoveryPhase(data["phase"]),
                task_status=data.get("task_status"),
                connection_state=data.get("connection_state"),
                recoverable=data.get("recoverable", False),
                retry_attempt=data.get("retry_attempt", 0),
                retry_limit=data.get("retry_limit"),
                reason=data.get("reason", ""),
                error=data.get("error"),
                updated_at=data.get("updated_at"),
                sequence=data.get("sequence", 0),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(
                "Invalid Agent recovery state structure"
            ) from exc


__all__ = ["AgentRecoveryStateStorage"]
