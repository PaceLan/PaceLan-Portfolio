"""Page and panel transition contracts for the M22 visual interaction layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TransitionPhase(str, Enum):
    """Lifecycle phases for a page/panel transition."""

    IDLE = "idle"
    EXITING = "exiting"
    ENTERING = "entering"
    COMPLETE = "complete"


class TransitionDirection(str, Enum):
    """Logical direction of a panel/page transition."""

    NONE = "none"
    FORWARD = "forward"
    BACKWARD = "backward"


@dataclass(frozen=True)
class PanelTransition:
    """Immutable description of one page/panel transition."""

    source: Optional[str] = None
    target: Optional[str] = None
    direction: TransitionDirection = TransitionDirection.NONE
    duration_ms: int = 180
    phase: TransitionPhase = TransitionPhase.IDLE

    def __post_init__(self) -> None:
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")

    @property
    def active(self) -> bool:
        """Return whether the transition is currently active."""
        return self.phase in (
            TransitionPhase.EXITING,
            TransitionPhase.ENTERING,
        )


class PanelTransitionController:
    """Small deterministic state machine for page/panel transitions."""

    def __init__(self, duration_ms: int = 180) -> None:
        if duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")

        self._duration_ms = duration_ms
        self._current_panel: Optional[str] = None
        self._transition = PanelTransition(duration_ms=duration_ms)

    @property
    def current_panel(self) -> Optional[str]:
        return self._current_panel

    @property
    def transition(self) -> PanelTransition:
        return self._transition

    def start(
        self,
        target: str,
        *,
        direction: TransitionDirection = TransitionDirection.NONE,
    ) -> PanelTransition:
        """Start a deterministic transition toward ``target``."""
        if not target:
            raise ValueError("target must not be empty")

        source = self._current_panel

        if source == target:
            self._transition = PanelTransition(
                source=source,
                target=target,
                direction=direction,
                duration_ms=self._duration_ms,
                phase=TransitionPhase.COMPLETE,
            )
            return self._transition

        self._transition = PanelTransition(
            source=source,
            target=target,
            direction=direction,
            duration_ms=self._duration_ms,
            phase=(
                TransitionPhase.EXITING
                if source is not None
                else TransitionPhase.ENTERING
            ),
        )
        return self._transition

    def enter(self) -> PanelTransition:
        """Advance an active transition into its entering phase."""
        if self._transition.target is None:
            return self._transition

        self._transition = PanelTransition(
            source=self._transition.source,
            target=self._transition.target,
            direction=self._transition.direction,
            duration_ms=self._transition.duration_ms,
            phase=TransitionPhase.ENTERING,
        )
        return self._transition

    def complete(self) -> PanelTransition:
        """Complete the current transition and commit its target panel."""
        target = self._transition.target

        if target is not None:
            self._current_panel = target

        self._transition = PanelTransition(
            source=self._transition.source,
            target=target,
            direction=self._transition.direction,
            duration_ms=self._transition.duration_ms,
            phase=TransitionPhase.COMPLETE,
        )
        return self._transition

    def reset(self) -> PanelTransition:
        """Return the controller to an idle state."""
        self._transition = PanelTransition(
            duration_ms=self._duration_ms,
        )
        return self._transition


__all__ = [
    "PanelTransition",
    "PanelTransitionController",
    "TransitionDirection",
    "TransitionPhase",
]
