from __future__ import annotations

from application.history import (
    AgentHistoryEntry,
    AgentHistoryStatus,
    AgentHistoryStore,
)
from application.models import ApplicationExecutionModel
from application.verification import VerificationResult


class AgentHistoryRecorder:
    """Records an application execution into Agent lifecycle history."""

    def __init__(self, store: AgentHistoryStore | None = None) -> None:
        self.store = store if store is not None else AgentHistoryStore()

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

        return self.store.append(entry)

    @staticmethod
    def _map_result_status(status: str) -> AgentHistoryStatus:
        try:
            return AgentHistoryStatus(status)
        except ValueError as exc:
            raise ValueError(
                f"Unsupported execution result status: {status}"
            ) from exc


__all__ = ["AgentHistoryRecorder"]
