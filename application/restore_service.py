from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from agent_workflow.project_context import ProjectContext

from application.context_persistence import ContextPersistenceService
from application.history import AgentHistoryEntry
from application.history_storage import AgentHistoryStorage
from application.models import ApplicationExecutionModel, ProjectModel
from application.project_storage import ProjectStorage
from application.workflow_storage import WorkflowStorage


@dataclass(frozen=True)
class ProjectRestoreState:
    """Complete persisted state available for one project."""

    project: ProjectModel
    workflow: ApplicationExecutionModel | None = None
    history: tuple[AgentHistoryEntry, ...] = ()
    context: ProjectContext | None = None


class RestoreService:
    """Unified B5 restore and persisted-context retrieval service."""

    def __init__(
        self,
        project_storage: ProjectStorage | None = None,
        workflow_storage: WorkflowStorage | None = None,
        history_storage: AgentHistoryStorage | None = None,
        context_persistence: ContextPersistenceService | None = None,
    ) -> None:
        self._project_storage = project_storage or ProjectStorage()
        self._workflow_storage = workflow_storage or WorkflowStorage()
        self._history_storage = history_storage or AgentHistoryStorage()
        self._context_persistence = (
            context_persistence or ContextPersistenceService()
        )

    def restore(self, project_path: str | Path) -> ProjectRestoreState:
        """Restore all persisted state that actually exists."""

        project = self._project_storage.load(project_path)

        workflow = (
            self._workflow_storage.load(project_path)
            if self._workflow_storage.exists(project_path)
            else None
        )

        history = (
            self._history_storage.load(project_path)
            if self._history_storage.exists(project_path)
            else ()
        )

        context = (
            self._context_persistence.load(project_path)
            if self._context_persistence.exists(project_path)
            else None
        )

        return ProjectRestoreState(
            project=project,
            workflow=workflow,
            history=history,
            context=context,
        )

    def load_project(self, project_path: str | Path) -> ProjectModel:
        return self._project_storage.load(project_path)

    def load_workflow(
        self,
        project_path: str | Path,
    ) -> ApplicationExecutionModel:
        return self._workflow_storage.load(project_path)

    def load_history(
        self,
        project_path: str | Path,
    ) -> tuple[AgentHistoryEntry, ...]:
        return self._history_storage.load(project_path)

    def load_context(self, project_path: str | Path) -> ProjectContext:
        return self._context_persistence.load(project_path)

    def has_project(self, project_path: str | Path) -> bool:
        return self._project_storage.exists(project_path)

    def has_workflow(self, project_path: str | Path) -> bool:
        return self._workflow_storage.exists(project_path)

    def has_history(self, project_path: str | Path) -> bool:
        return self._history_storage.exists(project_path)

    def has_context(self, project_path: str | Path) -> bool:
        return self._context_persistence.exists(project_path)


__all__ = ["ProjectRestoreState", "RestoreService"]
