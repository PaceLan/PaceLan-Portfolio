from __future__ import annotations

from application.models import ProjectGoal


class GoalAuthority:
    """Application-level authority for the active project goal."""

    def __init__(self) -> None:
        self._goal: ProjectGoal | None = None
        self._confirmed = False

    @property
    def goal(self) -> ProjectGoal | None:
        return self._goal

    @property
    def confirmed(self) -> bool:
        return self._goal is not None and self._confirmed

    def set_goal(self, goal: ProjectGoal) -> ProjectGoal:
        self._goal = goal
        self._confirmed = False
        return goal

    def confirm(self) -> ProjectGoal:
        if self._goal is None:
            raise ValueError("A project goal must exist before confirmation")
        self._confirmed = True
        return self._goal

    def require_confirmed(self) -> ProjectGoal:
        if not self.confirmed:
            raise ValueError("A confirmed project goal is required")
        return self._goal

    def clear(self) -> None:
        self._goal = None
        self._confirmed = False
