"""Immutable workspace composition definitions for the UI layer."""

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class NavigationLayout:
    """Stable navigation regions within the workspace."""

    regions: Tuple[str, ...] = ("projects", "tasks", "history")


@dataclass(frozen=True)
class MainWorkspaceLayout:
    """Primary workspace region."""

    region: str = "main_workspace"


@dataclass(frozen=True)
class StatusLayout:
    """Stable status and activity regions."""

    regions: Tuple[str, ...] = ("status", "execution", "activity")


@dataclass(frozen=True)
class WorkspaceLayout:
    """Immutable composition contract for the application workspace."""

    navigation: NavigationLayout = NavigationLayout()
    main_workspace: MainWorkspaceLayout = MainWorkspaceLayout()
    status: StatusLayout = StatusLayout()

    @property
    def regions(self) -> Tuple[str, ...]:
        """Return the stable top-level workspace composition."""
        return (
            "navigation",
            self.main_workspace.region,
            "status",
        )
