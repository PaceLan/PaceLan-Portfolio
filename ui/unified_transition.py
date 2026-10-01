"""Unified product-level visual transition coordination for M26.7."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .panel_transitions import (
    PanelTransition,
    PanelTransitionController,
    TransitionDirection,
    TransitionPhase,
)


class UnifiedTransitionKind(str, Enum):
    """Product-level visual transition contexts."""

    OPENING = "opening"
    LOADING = "loading"
    GREETING = "greeting"
    WORKSPACE = "workspace"
    THEME = "theme"


@dataclass(frozen=True)
class UnifiedTransition:
    """Immutable description of a product-level transition."""

    kind: UnifiedTransitionKind
    source: str | None
    target: str
    duration_ms: int
    phase: TransitionPhase

    @property
    def active(self) -> bool:
        return self.phase in (
            TransitionPhase.EXITING,
            TransitionPhase.ENTERING,
        )


class UnifiedTransitionController:
    """Coordinate product-level transitions through the existing panel engine."""

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
    ) -> UnifiedTransition:
        if not target:
            raise ValueError("target must not be empty")

        transition = self._panel.start(target, direction=direction)
        self._current_kind = kind

        return UnifiedTransition(
            kind=kind,
            source=transition.source,
            target=target,
            duration_ms=transition.duration_ms,
            phase=transition.phase,
        )

    def enter(self) -> UnifiedTransition:
        transition = self._panel.enter()
        return self._snapshot(transition)

    def complete(self) -> UnifiedTransition:
        transition = self._panel.complete()
        return self._snapshot(transition)

    def reset(self) -> UnifiedTransition | None:
        self._panel.reset()
        self._current_kind = None
        return None

    def _snapshot(self, transition: PanelTransition) -> UnifiedTransition:
        if self._current_kind is None:
            raise RuntimeError("no unified transition has been started")

        if transition.target is None:
            raise RuntimeError("unified transition has no target")

        return UnifiedTransition(
            kind=self._current_kind,
            source=transition.source,
            target=transition.target,
            duration_ms=transition.duration_ms,
            phase=transition.phase,
        )


__all__ = [
    "UnifiedTransitionKind",
    "UnifiedTransition",
    "UnifiedTransitionController",
]
