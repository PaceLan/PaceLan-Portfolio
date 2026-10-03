"""Application-layer registry for managing multiple projects."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Optional


@dataclass(frozen=True)
class RegisteredProject:
    """Application-owned identity for a registered project."""

    project_id: str
    path: Path


class ProjectRegistry:
    """Manage registered projects and the active project identity."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        self._projects: dict[str, RegisteredProject] = {}
        self._active_project_id: Optional[str] = None
        self._storage_path = (
            Path(storage_path).resolve()
            if storage_path is not None
            else None
        )

        if self._storage_path is not None and self._storage_path.is_file():
            self.load()

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

    def get_project(self, project_id: str) -> RegisteredProject:
        try:
            return self._projects[project_id]
        except KeyError as exc:
            raise KeyError(
                f"Unknown project_id: {project_id}"
            ) from exc

    def list_projects(self) -> tuple[RegisteredProject, ...]:
        return tuple(self._projects.values())

    def switch_project(self, project_id: str) -> RegisteredProject:
        project = self.get_project(project_id)
        self._active_project_id = project.project_id
        return project

    def remove_project(self, project_id: str) -> None:
        self.get_project(project_id)
        del self._projects[project_id]

        if self._active_project_id == project_id:
            self._active_project_id = next(
                iter(self._projects),
                None,
            )

    def save(self, storage_path: str | Path | None = None) -> Path:
        target = Path(storage_path).resolve() if storage_path else self._storage_path
        if target is None:
            raise ValueError("storage_path is required")

        payload = {
            "schema_version": 1,
            "active_project_id": self._active_project_id,
            "projects": [
                {
                    "project_id": project.project_id,
                    "path": str(project.path),
                }
                for project in self._projects.values()
            ],
        }

        target.parent.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=".registry.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        os.replace(temporary, target)
        self._storage_path = target
        return target

    def load(self, storage_path: str | Path | None = None) -> None:
        target = Path(storage_path).resolve() if storage_path else self._storage_path
        if target is None:
            raise ValueError("storage_path is required")

        with target.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        if payload.get("schema_version") != 1:
            raise ValueError(
                f"Unsupported registry schema: "
                f"{payload.get('schema_version')!r}"
            )

        projects: dict[str, RegisteredProject] = {}
        for item in payload.get("projects", []):
            project_id = item.get("project_id")
            project_path = item.get("path")

            if not isinstance(project_id, str) or not project_id:
                raise ValueError("Invalid persisted project_id")
            if not isinstance(project_path, str) or not project_path:
                raise ValueError("Invalid persisted project path")

            projects[project_id] = RegisteredProject(
                project_id=project_id,
                path=Path(project_path),
            )

        active = payload.get("active_project_id")
        if active is not None and active not in projects:
            raise ValueError("Persisted active project does not exist")

        self._projects = projects
        self._active_project_id = active
        self._storage_path = target
