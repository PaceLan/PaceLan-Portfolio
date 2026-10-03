"""Application-layer workflow persistence facade."""

from __future__ import annotations

from pathlib import Path

from .models import ApplicationExecutionModel
from .workflow_storage import WorkflowStorage


class WorkflowPersistenceService:
    """Application boundary for durable workflow state."""

    def __init__(
        self,
        storage: WorkflowStorage | None = None,
    ) -> None:
        if storage is not None and not isinstance(storage, WorkflowStorage):
            raise TypeError("storage must be a WorkflowStorage")

        self._storage = storage or WorkflowStorage()

    def exists(self, project_path: str | Path) -> bool:
        return self._storage.exists(project_path)

    def save(
        self,
        execution: ApplicationExecutionModel,
        project_path: str | Path,
    ) -> Path:
        if not isinstance(execution, ApplicationExecutionModel):
            raise TypeError(
                "execution must be an ApplicationExecutionModel"
            )

        return self._storage.save(execution, project_path)

    def load(
        self,
        project_path: str | Path,
    ) -> ApplicationExecutionModel:
        return self._storage.load(project_path)


__all__ = ["WorkflowPersistenceService"]
