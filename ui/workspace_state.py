"""Immutable workspace state models for the Coding Assistant UI."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class SelectedFile:
    """Currently selected project file."""

    path: Optional[str] = None


@dataclass(frozen=True)
class ViewerState:
    """Current read-only file viewer state."""

    path: Optional[str] = None
    contents: str = ""
    loaded: bool = False
    error: Optional[str] = None


@dataclass(frozen=True)
class TreeState:
    """Current project tree presentation state."""

    loaded: bool = False
    selected_path: Optional[str] = None
    selected_is_directory: bool = False


@dataclass(frozen=True)
class WorkspaceState:
    """Immutable UI state spanning project, tree, viewer and status."""

    project: object
    tree: TreeState = TreeState()
    selected_file: SelectedFile = SelectedFile()
    viewer: ViewerState = ViewerState()
    status: str = "Ready"
