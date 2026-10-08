"""Deterministic page and panel transition primitives for PacePilot."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TransitionPhase(str, Enum):
    """Lifecycle phase of a transition."""

    IDLE = "idle"
    EXITING = "exiting"
    ENTERING = "entering"
    COMPLETE = "complete"


class TransitionDirection(str, Enum):
    """Logical navigation direction."""

    NONE = "none"
    FORWARD = "forward"
    BACKWARD = "backward"


class TransitionPrimitive(str, Enum):
    """Visual primitive used to communicate a transition."""

    CROSS_FADE = "cross_fade"
    AMBIENT_SHIFT = "ambient_shift"
    FOCUS_DEPTH = "focus_depth"


@dataclass(frozen=True)
class PanelTransition:
    """Immutable description of one panel transition."""

    source: Optional[str] = None
    target: Optional[str] = None
    direction: TransitionDirection = TransitionDirection.NONE
    primitive: TransitionPrimitive = TransitionPrimitive.CROSS_FADE
    duration_ms: int = 180
    phase: TransitionPhase = TransitionPhase.IDLE

    def __post_init__(self) -> None:
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")

    @property
    def active(self) -> bool:
        return self.phase in (
            TransitionPhase.EXITING,
            TransitionPhase.ENTERING,
        )


class PanelTransitionController:
    """Small deterministic state machine for visual transitions."""

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
        primitive: TransitionPrimitive = TransitionPrimitive.CROSS_FADE,
    ) -> PanelTransition:
        """Start a transition toward target."""
        if not target:
            raise ValueError("target must not be empty")

        source = self._current_panel

        if source == target:
            self._transition = PanelTransition(
                source=source,
                target=target,
                direction=direction,
                primitive=primitive,
                duration_ms=self._duration_ms,
                phase=TransitionPhase.COMPLETE,
            )
            return self._transition

        phase = (
            TransitionPhase.EXITING
            if source is not None
            else TransitionPhase.ENTERING
        )

        self._transition = PanelTransition(
            source=source,
            target=target,
            direction=direction,
            primitive=primitive,
            duration_ms=self._duration_ms,
            phase=phase,
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
            primitive=self._transition.primitive,
            duration_ms=self._transition.duration_ms,
            phase=TransitionPhase.ENTERING,
        )
        return self._transition

    def complete(self) -> PanelTransition:
        """Complete the transition and commit its target panel."""
        target = self._transition.target

        if target is not None:
            self._current_panel = target

        self._transition = PanelTransition(
            source=self._transition.source,
            target=target,
            direction=self._transition.direction,
            primitive=self._transition.primitive,
            duration_ms=self._duration_ms,
            phase=TransitionPhase.COMPLETE,
        )
        return self._transition

    def reset(self) -> PanelTransition:
        """Return the controller to its initial state."""
        self._current_panel = None
        self._transition = PanelTransition(duration_ms=self._duration_ms)
        return self._transition


__all__ = [
    "PanelTransition",
    "PanelTransitionController",
    "TransitionDirection",
    "TransitionPhase",
    "TransitionPrimitive",
]
