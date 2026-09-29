"""Application-level coordination for the Coding Assistant UI."""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from application.workspace import (
    ApplicationTreeNode,
    ProjectTreeProvider,
    FileReaderProvider,
    ProjectWorkspaceService,
)
from ui.workspace_state import (
    SelectedFile,
    TreeState,
    ViewerState,
    WorkspaceState,
)


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
    """UI adapter over the Application workspace boundary."""

    def __init__(
        self,
        project_manager=None,
        tree_provider: Optional[ProjectTreeProvider] = None,
        file_reader: Optional[FileReaderProvider] = None,
        workspace: Optional[ProjectWorkspaceService] = None,
    ) -> None:
        self.workspace = workspace or ProjectWorkspaceService(
            project_manager=project_manager,
            tree_provider=tree_provider,
            file_reader=file_reader,
        )
        self._project_context = ProjectContext(None, None, False, False)

    @property
    def project_context(self) -> ProjectContext:
        return self._project_context

    def open_project(self, path: Union[str, Path]) -> ProjectContext:
        info = self.workspace.open_project(path)

        self._project_context = ProjectContext(
            name=info["project_name"],
            path=info["project_path"],
            exists=bool(info["exists"]),
            is_directory=bool(info["is_directory"]),
        )

        return self._project_context

    def get_project_tree(self) -> ApplicationTreeNode:
        return self.workspace.build_tree_model()

    def select_file(
        self,
        relative_path: Union[str, Path],
    ) -> FileLoadResult:
        display_path = Path(relative_path).as_posix()

        try:
            contents = self.workspace.read_file(relative_path)
        except (
            FileNotFoundError,
            IsADirectoryError,
            UnicodeDecodeError,
            ValueError,
        ) as error:
            return FileLoadResult(
                display_path,
                False,
                error=str(error),
            )

        return FileLoadResult(
            display_path,
            True,
            contents=contents,
        )

    def initial_state(self) -> WorkspaceState:
        return WorkspaceState(
            project=self._project_context,
            tree=TreeState(),
            selected_file=SelectedFile(),
            viewer=ViewerState(),
            status="Ready",
        )
