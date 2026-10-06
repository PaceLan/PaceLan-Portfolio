"""Atomic persistence for execution contexts."""
import json
import os
from pathlib import Path

from application.execution_context import ExecutionContext


SCHEMA_VERSION = 1


class ExecutionContextStorage:
    def __init__(self, project_path: str | Path):
        self._project_path = Path(project_path)

    @property
    def storage_path(self) -> Path:
        return self._project_path / ".pacepilot" / "execution_context.json"

    def save(self, context: ExecutionContext) -> None:
        if not isinstance(context, ExecutionContext):
            raise TypeError("context must be an ExecutionContext")

        path = self.storage_path
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = self._serialize(context)
        temp_path = path.with_name(path.name + ".tmp")

        temp_path.write_text(
            json.dumps(payload, indent=2, sort_keys=True),
            encoding="utf-8",
        )
        os.replace(temp_path, path)

    def load(self) -> ExecutionContext | None:
        path = self.storage_path
        if not path.exists():
            return None

        payload = json.loads(path.read_text(encoding="utf-8"))

        if payload.get("schema_version") != SCHEMA_VERSION:
            raise ValueError("unsupported execution context schema")

        return self._deserialize(payload["context"])

    @staticmethod
    def _serialize(context: ExecutionContext) -> dict:
        return {
            "schema_version": SCHEMA_VERSION,
            "context": {
                "project_id": context.project_id,
                "task_id": context.task_id,
                "run_id": context.run_id,
                "step_id": context.step_id,
                "command_id": context.command_id,
                "workflow_id": context.workflow_id,
                "process_id": context.process_id,
                "process_state": context.process_state,
                "terminal_id": context.terminal_id,
                "terminal_session_id": context.terminal_session_id,
                "terminal_state": context.terminal_state,
                "execution_state": context.execution_state,
                "recoverability": context.recoverability,
                "checkpoint_sequence": context.checkpoint_sequence,
                "checkpointed_at": (
                    context.checkpointed_at.isoformat()
                    if context.checkpointed_at is not None
                    else None
                ),
            },
        }

    @staticmethod
    def _deserialize(data: dict) -> ExecutionContext:
        from datetime import datetime

        checkpointed_at = data.get("checkpointed_at")
        if checkpointed_at is not None:
            checkpointed_at = datetime.fromisoformat(checkpointed_at)

        return ExecutionContext(
            project_id=data["project_id"],
            task_id=data["task_id"],
            run_id=data["run_id"],
            step_id=data["step_id"],
            command_id=data.get("command_id"),
            workflow_id=data.get("workflow_id"),
            process_id=data.get("process_id"),
            process_state=data.get("process_state"),
            terminal_id=data.get("terminal_id"),
            terminal_session_id=data.get("terminal_session_id"),
            terminal_state=data.get("terminal_state"),
            execution_state=data.get("execution_state", "UNKNOWN"),
            recoverability=data.get("recoverability", "UNKNOWN"),
            checkpoint_sequence=data.get("checkpoint_sequence", 0),
            checkpointed_at=checkpointed_at,
        )

    def update(self, context: ExecutionContext) -> None:
        current = self.load()

        if (
            current is not None
            and context.checkpoint_sequence < current.checkpoint_sequence
        ):
            raise ValueError(
                "stale execution context cannot replace newer checkpoint"
            )

        self.save(context)
