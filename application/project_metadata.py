"""Application-layer persistence for project metadata."""

from __future__ import annotations

import json
from pathlib import Path

from .models import ProjectGoal, ProjectModel


class ProjectMetadataService:
    """Persist and restore Application-owned project metadata."""

    DIRECTORY_NAME = ".pacepilot"
    FILE_NAME = "project.json"

    @classmethod
    def metadata_path(cls, project_path: str | Path) -> Path:
        return Path(project_path).resolve() / cls.DIRECTORY_NAME / cls.FILE_NAME

    @classmethod
    def save(cls, project: ProjectModel, project_path: str | Path) -> None:
        path = cls.metadata_path(project_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        payload = {
            "project_id": project.project_id,
            "goal": project.goal.text,
        }

        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    @classmethod
    def load(
        cls,
        project_path: str | Path,
        project_id: str,
    ) -> ProjectModel:
        path = cls.metadata_path(project_path)

        if not path.exists():
            return ProjectModel(project_id=project_id)

        payload = json.loads(path.read_text(encoding="utf-8"))

        stored_project_id = payload.get("project_id", project_id)
        if stored_project_id != project_id:
            raise ValueError(
                "Project metadata project_id does not match the requested project"
            )

        return ProjectModel(
            project_id=project_id,
            goal=ProjectGoal(text=payload.get("goal", "")),
        )
