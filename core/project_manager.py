from pathlib import Path
from typing import Dict, Optional, Union

from agent_workflow.project_scanner import (
    ProjectScanResult,
    ProjectScanner,
)


class ProjectManager:
    def __init__(self) -> None:
        self._project_path: Optional[Path] = None

    def open_project(self, path: Union[str, Path]) -> None:
        self._project_path = Path(path).resolve()

    def get_project_path(self) -> Optional[Path]:
        return self._project_path

    def get_project_info(self) -> Dict[str, object]:
        if self._project_path is None:
            return {
                "project_name": None,
                "project_path": None,
                "exists": False,
                "is_directory": False,
            }

        return {
            "project_name": self._project_path.name,
            "project_path": self._project_path,
            "exists": self._project_path.exists(),
            "is_directory": self._project_path.is_dir(),
        }

    def scan_project(self) -> ProjectScanResult:
        """Scan the currently opened project."""

        if self._project_path is None:
            raise FileNotFoundError(
                "No project is currently open."
            )

        return ProjectScanner(self._project_path).scan()