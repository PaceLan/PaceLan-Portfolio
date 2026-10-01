from pathlib import Path
from typing import Optional, Protocol, Union
from dataclasses import dataclass

from core.file_reader import FileReader
from core.project_manager import ProjectManager
from core.project_tree import ProjectTree, ProjectTreeNode


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

    @property
    def project_path(self) -> Optional[Path]:
        return self._project_path

    def open_project(self, path: Union[str, Path]) -> dict[str, object]:
        self.project_manager.open_project(path)
        info = self.project_manager.get_project_info()
        self._project_path = info["project_path"]

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
        self._file_reader = None
        self._tree_provider = None
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

