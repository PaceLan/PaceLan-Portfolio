"""Application-layer registry for managing multiple projects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass(frozen=True)
class RegisteredProject:
    """Application-owned identity for a registered project."""

    project_id: str
    path: Path


class ProjectRegistry:
    """Manage registered projects and the active project identity."""

    def __init__(self) -> None:
        self._projects: dict[str, RegisteredProject] = {}
        self._active_project_id: Optional[str] = None

    @property
    def active_project_id(self) -> Optional[str]:
        return self._active_project_id

    def register_project(
        self,
        project_id: str,
        path: str | Path,
    ) -> RegisteredProject:
        if not isinstance(project_id, str) or not project_id:
            raise ValueError("project_id must be a non-empty string")

        project_path = Path(path).resolve()

        existing = self._projects.get(project_id)
        if existing is not None and existing.path != project_path:
            raise ValueError(
                f"project_id is already registered: {project_id}"
            )

        project = RegisteredProject(
            project_id=project_id,
            path=project_path,
        )
        self._projects[project_id] = project

        if self._active_project_id is None:
            self._active_project_id = project_id

        return project

    def list_projects(self) -> tuple[RegisteredProject, ...]:
        return tuple(self._projects.values())

    def get_project(self, project_id: str) -> RegisteredProject:
        try:
            return self._projects[project_id]
        except KeyError as exc:
            raise KeyError(f"Unknown project_id: {project_id}") from exc

    def switch_project(self, project_id: str) -> RegisteredProject:
        project = self.get_project(project_id)
        self._active_project_id = project.project_id
        return project

    def remove_project(self, project_id: str) -> None:
        self.get_project(project_id)
        del self._projects[project_id]

        if self._active_project_id == project_id:
            self._active_project_id = (
                next(iter(self._projects), None)
            )
