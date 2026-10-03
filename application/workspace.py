from pathlib import Path
from typing import Optional, Protocol, Union
from dataclasses import dataclass

from core.file_reader import FileReader
from core.project_manager import ProjectManager
from core.project_tree import ProjectTree, ProjectTreeNode
from application.models import ProjectGoal, ProjectModel
from application.project_metadata import ProjectMetadataService
from application.project_storage import ProjectStorage
from application.task_management import (
    ProductTask,
    TaskManagementService,
)


@dataclass(frozen=True)
class ApplicationTreeNode:
    """Application-owned tree representation exposed to product interfaces."""

    name: str
    path: Path
    is_directory: bool
    children: tuple["ApplicationTreeNode", ...] = ()


class ProjectTreeProvider(Protocol):
    def build_tree(self) -> ProjectTreeNode:
        """Build and return a project tree."""


class FileReaderProvider(Protocol):
    def read_file(self, relative_path: Union[str, Path]) -> str:
        """Read one project-relative text file."""


class ProjectWorkspaceService:
    """Application boundary for project workspace operations."""

    def __init__(
        self,
        project_manager: Optional[ProjectManager] = None,
        tree_provider: Optional[ProjectTreeProvider] = None,
        file_reader: Optional[FileReaderProvider] = None,
    ) -> None:
        self.project_manager = project_manager or ProjectManager()
        self._tree_provider = tree_provider
        self._file_reader = file_reader
        self._project_path: Optional[Path] = None
        self._project_model: Optional[ProjectModel] = None
        self._task_service = TaskManagementService()
        self._project_storage = ProjectStorage()

    @property
    def project_path(self) -> Optional[Path]:
        return self._project_path

    @property
    def project_model(self) -> Optional[ProjectModel]:
        return self._project_model

    @property
    def tasks(self) -> tuple[ProductTask, ...]:
        if self._project_model is None:
            return ()
        return self._task_service.list_for_project(
            self._project_model.project_id
        )

    def create_task(
        self,
        title: str,
        description: str = "",
        *,
        task_id: str | None = None,
    ) -> ProductTask:
        if self._project_model is None:
            raise ValueError(
                "A valid project must be open before creating a task"
            )

        return self._task_service.create(
            self._project_model.project_id,
            title,
            description,
            task_id=task_id,
        )

    def get_task(self, task_id: str) -> ProductTask:
        return self._task_service.get(task_id)

    def attach_task_plan(self, task_id: str, plan_id: str) -> ProductTask:
        if self._project_model is None:
            raise ValueError("No project is open")

        try:
            task = self._task_service.get(task_id)
        except KeyError as exc:
            raise ValueError("Task does not belong to the active project") from exc

        if task.project_id != self._project_model.project_id:
            raise ValueError("Task does not belong to the active project")

        if not isinstance(plan_id, str) or not plan_id.strip():
            raise ValueError("plan_id must be a non-empty string")

        return self._task_service.attach_plan(task_id, plan_id)

    def submit_task(self, task_id: str) -> ProductTask:
        return self._task_service.submit(task_id)

    def start_task(self, task_id: str) -> ProductTask:
        return self._task_service.start(task_id)

    def complete_task(self, task_id: str) -> ProductTask:
        return self._task_service.complete(task_id)

    def fail_task(self, task_id: str) -> ProductTask:
        return self._task_service.fail(task_id)

    def block_task(self, task_id: str) -> ProductTask:
        return self._task_service.block(task_id)

    def cancel_task(self, task_id: str) -> ProductTask:
        return self._task_service.cancel(task_id)

    @property
    def project_goal(self) -> Optional[ProjectGoal]:
        if self._project_model is None:
            return None
        return self._project_model.goal

    def update_project_goal(self, goal: str) -> ProjectGoal:
        if self._project_model is None:
            raise ValueError(
                "A valid project must be open before updating its goal"
            )

        normalized_goal = ProjectGoal(text=goal.strip())
        self._project_model = ProjectModel(
            project_id=self._project_model.project_id,
            goal=normalized_goal,
        )
        return normalized_goal

    def open_project(self, path: Union[str, Path]) -> dict[str, object]:
        self.project_manager.open_project(path)
        info = self.project_manager.get_project_info()
        self._project_path = info["project_path"]

        if self._project_path is not None:
            if self._project_storage.exists(self._project_path):
                self._project_model = self._project_storage.load(
                    self._project_path
                )
            else:
                self._project_model = ProjectMetadataService.load(
                    self._project_path,
                    self._project_path.name,
                )

        if self._file_reader is None and self._project_path is not None:
            self._file_reader = FileReader(self._project_path)

        return info

    def build_tree(self) -> ProjectTreeNode:
        project_path = self._project_path

        if project_path is None:
            raise ValueError(
                "A valid project must be open before building its tree"
            )

        info = self.project_manager.get_project_info()

        if (
            not bool(info["exists"])
            or not bool(info["is_directory"])
        ):
            raise ValueError(
                "A valid project must be open before building its tree"
            )

        provider = self._tree_provider or ProjectTree(project_path)
        return provider.build_tree()

    def build_tree_model(self) -> ApplicationTreeNode:
        """Build an Application-owned tree model for UI consumption."""

        return self._to_application_tree(self.build_tree())

    @classmethod
    def _to_application_tree(
        cls,
        node: ProjectTreeNode,
    ) -> ApplicationTreeNode:
        return ApplicationTreeNode(
            name=node.name,
            path=node.path,
            is_directory=node.is_directory,
            children=tuple(
                cls._to_application_tree(child)
                for child in node.children
            ),
        )

    def read_file(self, relative_path: Union[str, Path]) -> str:
        project_path = self._project_path

        if project_path is None:
            raise ValueError(
                "A valid project must be open before loading a file"
            )

        info = self.project_manager.get_project_info()

        if (
            not bool(info["exists"])
            or not bool(info["is_directory"])
        ):
            raise ValueError(
                "A valid project must be open before loading a file"
            )

        if self._file_reader is None:
            self._file_reader = FileReader(project_path)

        return self._file_reader.read_file(relative_path)

    def close_project(self) -> None:
        """Close the current project and clear workspace-local state."""
        self._project_path = None
        self._project_model = None
        self._file_reader = None
        self._tree_provider = None
        self._task_service = TaskManagementService()
        self.project_manager = type(self.project_manager)()

    def persist_project(self):
        """Persist the current project state as a recoverable snapshot."""
        project_path = self._project_path

        if project_path is None:
            raise ValueError(
                "A valid project must be open before persisting"
            )

        info = self.project_manager.get_project_info()
        if not bool(info.get("exists", False)) or not bool(
            info.get("is_directory", False)
        ):
            raise ValueError(
                "A valid project must be open before persisting"
            )

        from history.history_core import HistoryEntry, HistoryStore
        from snapshots.snapshot_service import SnapshotService
        from datetime import datetime, timezone

        snapshot = SnapshotService(project_path).create_snapshot()

        if self._project_model is not None:
            self._project_storage.save(
                self._project_model,
                project_path,
                name=project_path.name,
            )

        history_directory = project_path / "history"
        history_directory.mkdir(parents=True, exist_ok=True)
        HistoryStore(history_directory).append(
            HistoryEntry(
                timestamp=datetime.now(timezone.utc).isoformat(),
                operation="persist_project",
                target=str(project_path),
                result=snapshot.snapshot_id,
                success=True,
            )
        )
        return snapshot

    def reopen_project(self):
        """Reopen the previously active project."""
        if self._project_path is None:
            raise ValueError(
                "No previously opened project is available to reopen"
            )

        project_path = self._project_path
        self.close_project()
        return self.open_project(project_path)

