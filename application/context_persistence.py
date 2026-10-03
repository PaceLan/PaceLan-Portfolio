"""Application-layer facade for durable ProjectContext."""

from __future__ import annotations

from pathlib import Path

from agent_workflow.project_context import ProjectContext

from .context_storage import ContextStorage


class ContextPersistenceService:
    """Application boundary for durable project context."""

    def __init__(
        self,
        storage: ContextStorage | None = None,
    ) -> None:
        if storage is not None and not isinstance(storage, ContextStorage):
            raise TypeError("storage must be a ContextStorage")

        self._storage = storage or ContextStorage()

    def exists(self, project_path: str | Path) -> bool:
        return self._storage.exists(project_path)

    def save(
        self,
        context: ProjectContext,
        project_path: str | Path,
    ) -> Path:
        if not isinstance(context, ProjectContext):
            raise TypeError("context must be a ProjectContext")

        return self._storage.save(context, project_path)

    def load(self, project_path: str | Path) -> ProjectContext:
        return self._storage.load(project_path)


__all__ = ["ContextPersistenceService"]
