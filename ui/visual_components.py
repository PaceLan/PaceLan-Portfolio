"""Immutable visual component role definitions for the UI layer."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Panel:
    """Visual component representing a panel."""

    visual_role: str = "panel"


@dataclass(frozen=True)
class Navigation:
    """Visual component representing navigation."""

    visual_role: str = "navigation"


@dataclass(frozen=True)
class Status:
    """Visual component representing status information."""

    visual_role: str = "status"


@dataclass(frozen=True)
class Workspace:
    """Visual component representing the primary workspace."""

    visual_role: str = "workspace"


@dataclass(frozen=True)
class State:
    """Visual component representing UI state."""

    visual_role: str = "state"
