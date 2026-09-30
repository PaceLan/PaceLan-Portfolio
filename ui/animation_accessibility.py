"""Accessibility and performance policies for the M22 animation layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ui.animation import AnimationKind, AnimationRequest, AnimationSpec


class MotionMode(str, Enum):
    """User-facing motion preference."""

    NORMAL = "normal"
    REDUCED = "reduced"


@dataclass(frozen=True)
class MotionPolicy:
    """Presentation-only policy for adapting animation motion."""

    mode: MotionMode = MotionMode.NORMAL
    reduced_duration_ms: int = 0
    reduced_steps: int = 1
    max_duration_ms: int = 1000
    max_steps: int = 60

    def __post_init__(self) -> None:
        if self.reduced_duration_ms < 0:
            raise ValueError("reduced_duration_ms must be non-negative")
        if self.reduced_steps < 1:
            raise ValueError("reduced_steps must be positive")
        if self.max_duration_ms < 0:
            raise ValueError("max_duration_ms must be non-negative")
        if self.max_steps < 1:
            raise ValueError("max_steps must be positive")


@dataclass(frozen=True)
class PerformanceSnapshot:
    """Deterministic snapshot of animation workload."""

    active_animations: int = 0
    history_items: int = 0
    workspace_operations: int = 0

    @property
    def high_frequency(self) -> bool:
        return self.workspace_operations > 60

    @property
    def concurrent(self) -> bool:
        return self.active_animations > 1

    @property
    def large_history(self) -> bool:
        return self.history_items > 500


class AnimationAccessibility:
    """Adapt animation specifications without changing workflow state."""

    def __init__(self, policy: MotionPolicy | None = None) -> None:
        self.policy = policy or MotionPolicy()

    @property
    def reduced_motion(self) -> bool:
        return self.policy.mode is MotionMode.REDUCED

    def adapt_spec(self, spec: AnimationSpec) -> AnimationSpec:
        """Return a motion-safe presentation specification."""
        duration = min(spec.duration_ms, self.policy.max_duration_ms)
        steps = min(spec.steps, self.policy.max_steps)

        if self.reduced_motion:
            return AnimationSpec(
                kind=AnimationKind.NONE,
                duration_ms=self.policy.reduced_duration_ms,
                steps=self.policy.reduced_steps,
            )

        return AnimationSpec(
            kind=spec.kind,
            duration_ms=duration,
            steps=steps,
        )

    def adapt_request(self, request: AnimationRequest) -> AnimationRequest:
        """Apply the motion policy to an existing animation request."""
        return AnimationRequest(
            source=request.source,
            target=request.target,
            spec=self.adapt_spec(request.spec),
        )


class AnimationPerformanceGuard:
    """Presentation-layer sanity guard for animation workload."""

    def __init__(
        self,
        *,
        max_active_animations: int = 4,
        max_history_items: int = 5000,
    ) -> None:
        if max_active_animations < 1:
            raise ValueError("max_active_animations must be positive")
        if max_history_items < 0:
            raise ValueError("max_history_items must be non-negative")

        self.max_active_animations = max_active_animations
        self.max_history_items = max_history_items

    def normalize(self, snapshot: PerformanceSnapshot) -> PerformanceSnapshot:
        """Clamp workload metrics to deterministic UI-safe bounds."""
        return PerformanceSnapshot(
            active_animations=min(
                max(snapshot.active_animations, 0),
                self.max_active_animations,
            ),
            history_items=min(
                max(snapshot.history_items, 0),
                self.max_history_items,
            ),
            workspace_operations=max(snapshot.workspace_operations, 0),
        )

    def should_suppress_ambient(self, snapshot: PerformanceSnapshot) -> bool:
        """Suppress non-informational ambient effects under UI pressure."""
        return (
            snapshot.concurrent
            or snapshot.high_frequency
            or snapshot.large_history
        )


__all__ = [
    "AnimationAccessibility",
    "AnimationPerformanceGuard",
    "MotionMode",
    "MotionPolicy",
    "PerformanceSnapshot",
]
