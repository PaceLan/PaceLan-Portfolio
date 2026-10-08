from __future__ import annotations

from pathlib import Path

from application.history import (
    AgentHistoryEntry,
    AgentHistoryStatus,
    AgentHistoryStore,
)
from application.history_storage import AgentHistoryStorage
from application.models import ApplicationExecutionModel
from application.verification import VerificationResult


class AgentHistoryRecorder:
    """Records an application execution into Agent lifecycle history."""

    def __init__(
        self,
        store: AgentHistoryStore | None = None,
        *,
        storage: AgentHistoryStorage | None = None,
        project_path: str | Path | None = None,
    ) -> None:
        if store is not None and not isinstance(store, AgentHistoryStore):
            raise TypeError("store must be an AgentHistoryStore")

        if storage is not None and not isinstance(
            storage, AgentHistoryStorage
        ):
            raise TypeError("storage must be an AgentHistoryStorage")

        if project_path is not None and storage is None:
            storage = AgentHistoryStorage()

        if project_path is not None:
            project_path = Path(project_path).resolve()
            if not project_path.exists() or not project_path.is_dir():
                raise ValueError("project_path must be an existing directory")

        self.store = store if store is not None else AgentHistoryStore()
        self.storage = storage
        self.project_path = project_path

        if self.storage is not None and self.project_path is not None:
            existing = self.storage.load(self.project_path)
            for entry in existing:
                self.store.append(entry)

    def record_execution(
        self,
        execution: ApplicationExecutionModel,
        verification: VerificationResult,
        *,
        history_id: str,
        timestamp: str | None = None,
    ) -> AgentHistoryEntry:
        if not isinstance(execution, ApplicationExecutionModel):
            raise TypeError(
                "execution must be an ApplicationExecutionModel"
            )

        if not isinstance(verification, VerificationResult):
            raise TypeError("verification must be a VerificationResult")

        if execution.run.run_id != verification.run_id:
            raise ValueError(
                "execution and verification must reference the same run_id"
            )

        entry = AgentHistoryEntry.create(
            history_id=history_id,
            project_id=execution.task.project_id,
            task_id=execution.task.task_id,
            execution_id=execution.run.run_id,
            verification_status=verification.status.value,
            result_status=self._map_result_status(execution.result.status),
            timestamp=timestamp,
        )

        recorded = self.store.append(entry)

        if self.storage is not None and self.project_path is not None:
            self.storage.save(
                self.store.list_all(),
                self.project_path,
            )

        return recorded

    @staticmethod
    def _map_result_status(status: str) -> AgentHistoryStatus:
        if isinstance(status, AgentHistoryStatus):
            return status

        normalized = str(status).strip().lower()

        aliases = {
            "completed": AgentHistoryStatus.COMPLETED,
            "failed": AgentHistoryStatus.FAILED,
            "blocked": AgentHistoryStatus.BLOCKED,
            "cancelled": AgentHistoryStatus.CANCELLED,
            "canceled": AgentHistoryStatus.CANCELLED,
        }

        try:
            return aliases[normalized]
        except KeyError as exc:
            raise ValueError(
                f"Unsupported execution result status: {status}"
            ) from exc


__all__ = ["AgentHistoryRecorder"]
