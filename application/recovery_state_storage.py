from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path


SCHEMA_VERSION = 1


@dataclass(frozen=True)
class RecoveryState:
    recovery_id: str
    snapshot_id: str
    status: str
    reason: str
    sequence: int = 0


class RecoveryStateStorage:
    DIRECTORY_NAME = ".pacepilot"
    FILE_NAME = "recovery_state.json"

    def __init__(self, project_path: str | Path):
        self._project_path = Path(project_path)

    @property
    def storage_path(self) -> Path:
        return self._project_path / self.DIRECTORY_NAME / self.FILE_NAME

    def save(self, state: RecoveryState) -> None:
        if not isinstance(state, RecoveryState):
            raise TypeError("state must be a RecoveryState")

        current = self.load()
        if current is not None and state.sequence < current.sequence:
            raise ValueError("stale recovery state cannot replace newer state")

        path = self.storage_path
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "schema_version": SCHEMA_VERSION,
            "state": {
                "recovery_id": state.recovery_id,
                "snapshot_id": state.snapshot_id,
                "status": state.status,
                "reason": state.reason,
                "sequence": state.sequence,
            },
        }

        temporary = path.with_name(path.name + ".tmp")
        try:
            temporary.write_text(
                json.dumps(payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            os.replace(temporary, path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def load(self) -> RecoveryState | None:
        path = self.storage_path
        if not path.exists():
            return None

        payload = json.loads(path.read_text(encoding="utf-8"))

        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported recovery state schema")

        data = payload.get("state")
        if not isinstance(data, dict):
            raise ValueError("invalid recovery state payload")

        return RecoveryState(
            recovery_id=data["recovery_id"],
            snapshot_id=data["snapshot_id"],
            status=data["status"],
            reason=data["reason"],
            sequence=data.get("sequence", 0),
        )


__all__ = ["RecoveryState", "RecoveryStateStorage"]
