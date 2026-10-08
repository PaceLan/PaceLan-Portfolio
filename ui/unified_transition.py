"""Unified product-level visual transition coordination for PacePilot."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .panel_transitions import (
    PanelTransition,
    PanelTransitionController,
    TransitionDirection,
    TransitionPhase,
    TransitionPrimitive,
)


class UnifiedTransitionKind(str, Enum):
    """Product-level transition contexts."""

    OPENING = "opening"
    LOADING = "loading"
    GREETING = "greeting"
    WORKSPACE = "workspace"
    AGENT = "agent"
    RESULT = "result"
    THEME = "theme"


@dataclass(frozen=True)
class UnifiedTransition:
    """Immutable product-level transition snapshot."""

    kind: UnifiedTransitionKind
    source: str | None
    target: str
    duration_ms: int
    phase: TransitionPhase
    primitive: TransitionPrimitive

    @property
    def active(self) -> bool:
        return self.phase in (
            TransitionPhase.EXITING,
            TransitionPhase.ENTERING,
        )


class UnifiedTransitionController:
    """Single product-level entry point for visual transitions."""

    def __init__(self, duration_ms: int = 180) -> None:
        if duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")

        self._panel = PanelTransitionController(duration_ms=duration_ms)
        self._current_kind: UnifiedTransitionKind | None = None

    @property
    def current_kind(self) -> UnifiedTransitionKind | None:
        return self._current_kind

    @property
    def current_panel(self) -> str | None:
        return self._panel.current_panel

    @property
    def panel_transition(self) -> PanelTransition:
        return self._panel.transition

    def start(
        self,
        kind: UnifiedTransitionKind,
        target: str,
        *,
        direction: TransitionDirection = TransitionDirection.NONE,
        primitive: TransitionPrimitive = TransitionPrimitive.CROSS_FADE,
    ) -> UnifiedTransition:
        if not target:
            raise ValueError("target must not be empty")

        transition = self._panel.start(
            target,
            direction=direction,
            primitive=primitive,
        )
        self._current_kind = kind
        return self._snapshot(transition)

    def cross_fade(
        self,
        kind: UnifiedTransitionKind,
        target: str,
        *,
        direction: TransitionDirection = TransitionDirection.NONE,
    ) -> UnifiedTransition:
        return self.start(
            kind,
            target,
            direction=direction,
            primitive=TransitionPrimitive.CROSS_FADE,
        )

    def ambient_shift(
        self,
        kind: UnifiedTransitionKind,
        target: str,
        *,
        direction: TransitionDirection = TransitionDirection.NONE,
    ) -> UnifiedTransition:
        return self.start(
            kind,
            target,
            direction=direction,
            primitive=TransitionPrimitive.AMBIENT_SHIFT,
        )

    def focus_depth(
        self,
        kind: UnifiedTransitionKind,
        target: str,
        *,
        direction: TransitionDirection = TransitionDirection.NONE,
    ) -> UnifiedTransition:
        return self.start(
            kind,
            target,
            direction=direction,
            primitive=TransitionPrimitive.FOCUS_DEPTH,
        )

    def enter(self) -> UnifiedTransition:
        return self._snapshot(self._panel.enter())

    def complete(self) -> UnifiedTransition:
        return self._snapshot(self._panel.complete())

    def reset(self) -> None:
        self._panel.reset()
        self._current_kind = None

    def _snapshot(self, transition: PanelTransition) -> UnifiedTransition:
        if self._current_kind is None:
            raise RuntimeError("unified transition has no active kind")

        return UnifiedTransition(
            kind=self._current_kind,
            source=transition.source,
            target=transition.target or "",
            duration_ms=transition.duration_ms,
            phase=transition.phase,
            primitive=transition.primitive,
        )


__all__ = [
    "UnifiedTransitionKind",
    "UnifiedTransition",
    "UnifiedTransitionController",
]
