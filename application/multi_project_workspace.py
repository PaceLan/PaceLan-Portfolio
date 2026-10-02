from __future__ import annotations

from pathlib import Path
from typing import Optional

from .project_registry import ProjectRegistry, RegisteredProject
from .workspace import ProjectWorkspaceService


class MultiProjectWorkspaceService:
    """Coordinate project selection with the existing workspace service."""

    def __init__(
        self,
        registry: Optional[ProjectRegistry] = None,
        workspace: Optional[ProjectWorkspaceService] = None,
    ) -> None:
        self.registry = registry or ProjectRegistry()
        self.workspace = workspace or ProjectWorkspaceService()

    @property
    def active_project(self) -> Optional[RegisteredProject]:
        project_id = self.registry.active_project_id
        if project_id is None:
            return None
        return self.registry.get_project(project_id)

    def register_project(
        self,
        project_id: str,
        path: str | Path,
    ) -> RegisteredProject:
        return self.registry.register_project(project_id, path)

    def open_project(self, project_id: str) -> dict[str, object]:
        project = self.registry.switch_project(project_id)
        return self.workspace.open_project(project.path)

    def switch_project(self, project_id: str) -> dict[str, object]:
        return self.open_project(project_id)

    def close_project(self) -> None:
        self.workspace.close_project()

    def remove_project(self, project_id: str) -> None:
        if self.registry.active_project_id == project_id:
            self.workspace.close_project()
        self.registry.remove_project(project_id)
