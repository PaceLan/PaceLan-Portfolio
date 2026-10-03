"""Persistent application-owned storage for project state."""

from __future__ import annotations

import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any

from application.models import ProjectGoal, ProjectModel


class ProjectStorage:
    """Persist project identity and project-level state as JSON."""

    SCHEMA_VERSION = 1
    DIRECTORY_NAME = ".pacepilot"
    FILE_NAME = "project.json"

    def _storage_path(self, project_path: str | Path) -> Path:
        root = Path(project_path).resolve()
        return root / self.DIRECTORY_NAME / self.FILE_NAME

    def exists(self, project_path: str | Path) -> bool:
        return self._storage_path(project_path).is_file()

    def save(
        self,
        project: ProjectModel,
        project_path: str | Path,
        *,
        name: str | None = None,
        structure: Any = None,
        current_phase: str = "",
        current_task: str | None = None,
        next_task: str | None = None,
        completed: bool = False,
        blocked: bool = False,
    ) -> Path:
        if not isinstance(project, ProjectModel):
            raise TypeError("project must be a ProjectModel")

        root = Path(project_path).resolve()
        if not root.exists() or not root.is_dir():
            raise ValueError("project_path must be an existing directory")

        project_name = name if name is not None else root.name

        payload = {
            "schema_version": self.SCHEMA_VERSION,
            "project": {
                "project_id": project.project_id,
                "name": project_name,
                "path": str(root),
                "structure": structure,
            },
            "goal": {
                "current_goal": project.goal.text,
                "phase_goal": "",
            },
            "state": {
                "current_phase": current_phase,
                "current_task": current_task,
                "next_task": next_task,
                "completed": bool(completed),
                "blocked": bool(blocked),
            },
        }

        target = self._storage_path(root)
        target.parent.mkdir(parents=True, exist_ok=True)

        with NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=target.parent,
            prefix=".project.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temporary = Path(handle.name)
            json.dump(payload, handle, ensure_ascii=False, indent=2)
            handle.write("\n")

        os.replace(temporary, target)
        return target

    def load(self, project_path: str | Path) -> ProjectModel:
        target = self._storage_path(project_path)

        if not target.is_file():
            raise FileNotFoundError(
                f"Project storage does not exist: {target}"
            )

        try:
            with target.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Invalid project storage: {target}"
            ) from exc

        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported project storage schema: "
                f"{payload.get('schema_version')!r}"
            )

        project = payload.get("project")
        goal = payload.get("goal")

        if not isinstance(project, dict) or not isinstance(goal, dict):
            raise ValueError("Invalid project storage structure")

        project_id = project.get("project_id")
        current_goal = goal.get("current_goal", "")

        if not isinstance(project_id, str) or not project_id:
            raise ValueError("Invalid persisted project_id")

        if not isinstance(current_goal, str):
            raise ValueError("Invalid persisted current_goal")

        return ProjectModel(
            project_id=project_id,
            goal=ProjectGoal(text=current_goal),
        )

    def load_state(self, project_path: str | Path) -> dict[str, Any]:
        target = self._storage_path(project_path)

        if not target.is_file():
            raise FileNotFoundError(
                f"Project storage does not exist: {target}"
            )

        try:
            with target.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
        except (OSError, json.JSONDecodeError) as exc:
            raise ValueError(
                f"Invalid project storage: {target}"
            ) from exc

        if payload.get("schema_version") != self.SCHEMA_VERSION:
            raise ValueError(
                f"Unsupported project storage schema: "
                f"{payload.get('schema_version')!r}"
            )

        state = payload.get("state", {})
        return dict(state) if isinstance(state, dict) else {}
