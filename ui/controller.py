"""Application-level coordination for the Coding Assistant UI."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Protocol, Union

from core.file_reader import FileReader
from core.project_manager import ProjectManager
from core.project_tree import ProjectTree, ProjectTreeNode


class ProjectTreeProvider(Protocol):
    """Protocol for an injectable project-tree service."""

    def build_tree(self) -> ProjectTreeNode:
        """Build and return a project tree."""


class FileReaderProvider(Protocol):
    """Protocol for an injectable read-only file service."""

    def read_file(self, relative_path: Union[str, Path]) -> str:
        """Read one project-relative text file."""


@dataclass(frozen=True)
class ProjectContext:
    """Read-only project state prepared for presentation by the UI."""

    name: Optional[str]
    path: Optional[Path]
    exists: bool
    is_directory: bool


@dataclass(frozen=True)
class FileLoadResult:
    """Safe result returned when the controller loads a project file."""

    path: str
    success: bool
    contents: str = ""
    error: Optional[str] = None


class ApplicationController:
    """Coordinate UI state with existing project services."""

    def __init__(
        self,
        project_manager: Optional[ProjectManager] = None,
        tree_provider: Optional[ProjectTreeProvider] = None,
        file_reader: Optional[FileReaderProvider] = None,
    ) -> None:
        self.project_manager = project_manager or ProjectManager()
        self._tree_provider = tree_provider
        self._file_reader = file_reader
        self._project_context = ProjectContext(None, None, False, False)

    @property
    def project_context(self) -> ProjectContext:
        """Return the current project context without changing it."""
        return self._project_context

    def open_project(self, path: Union[str, Path]) -> ProjectContext:
        """Open a project through ProjectManager and retain its metadata."""
        self.project_manager.open_project(path)
        info = self.project_manager.get_project_info()
        self._project_context = ProjectContext(
            name=info["project_name"],
            path=info["project_path"],
            exists=bool(info["exists"]),
            is_directory=bool(info["is_directory"]),
        )
        if self._file_reader is None and self._project_context.path is not None:
            self._file_reader = FileReader(self._project_context.path)
        return self._project_context

    def get_project_tree(self) -> ProjectTreeNode:
        """Request the current project tree through ProjectTree."""
        project_path = self._project_context.path
        if (
            project_path is None
            or not self._project_context.exists
            or not self._project_context.is_directory
        ):
            raise ValueError("A valid project must be open before building its tree")

        provider = self._tree_provider or ProjectTree(project_path)
        return provider.build_tree()

    def select_file(self, relative_path: Union[str, Path]) -> FileLoadResult:
        """Load a selected project-relative file through FileReader."""
        project_path = self._project_context.path
        if (
            project_path is None
            or not self._project_context.exists
            or not self._project_context.is_directory
        ):
            raise ValueError("A valid project must be open before loading a file")
        if self._file_reader is None:
            self._file_reader = FileReader(project_path)

        display_path = Path(relative_path).as_posix()
        try:
            contents = self._file_reader.read_file(relative_path)
        except (FileNotFoundError, IsADirectoryError, UnicodeDecodeError, ValueError) as error:
            return FileLoadResult(display_path, False, error=str(error))
        return FileLoadResult(display_path, True, contents=contents)

    def initial_state(self) -> dict[str, object]:
        """Return deterministic UI startup state without filesystem writes."""
        return {
            "project": self._project_context,
            "tree_loaded": False,
            "content_placeholder": "Select a project item to inspect it.",
            "status": "Ready",
        }
