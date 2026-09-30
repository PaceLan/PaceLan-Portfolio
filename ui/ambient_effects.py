"""Ambient visual effects for the M22 animation layer."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AmbientEffect(str, Enum):
    """Supported ambient visual effects."""

    NONE = "none"
    BREATHING = "breathing"
    ACTIVITY = "activity"
    FOCUS = "focus"


class AmbientPhase(str, Enum):
    """Lifecycle state of an ambient effect."""

    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"


@dataclass(frozen=True)
class AmbientEffectState:
    """Immutable ambient-effect state."""

    effect: AmbientEffect = AmbientEffect.NONE
    phase: AmbientPhase = AmbientPhase.IDLE
    intensity: float = 0.0
    cycle_ms: int = 1200

    def __post_init__(self) -> None:
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("intensity must be between 0.0 and 1.0")
        if self.cycle_ms <= 0:
            raise ValueError("cycle_ms must be positive")

    @property
    def active(self) -> bool:
        return self.phase == AmbientPhase.ACTIVE


class AmbientEffectController:
    """Deterministic controller for subtle ambient UI effects."""

    def __init__(
        self,
        *,
        default_intensity: float = 0.35,
        cycle_ms: int = 1200,
    ) -> None:
        if not 0.0 <= default_intensity <= 1.0:
            raise ValueError("default_intensity must be between 0.0 and 1.0")
        if cycle_ms <= 0:
            raise ValueError("cycle_ms must be positive")

        self._default_intensity = default_intensity
        self._cycle_ms = cycle_ms
        self._state = AmbientEffectState(
            cycle_ms=cycle_ms,
        )

    @property
    def state(self) -> AmbientEffectState:
        return self._state

    def start(
        self,
        effect: AmbientEffect,
        *,
        intensity: float | None = None,
    ) -> AmbientEffectState:
        """Start an ambient effect."""
        if not isinstance(effect, AmbientEffect):
            raise TypeError("effect must be an AmbientEffect")

        value = (
            self._default_intensity
            if intensity is None
            else intensity
        )

        self._state = AmbientEffectState(
            effect=effect,
            phase=(
                AmbientPhase.IDLE
                if effect == AmbientEffect.NONE
                else AmbientPhase.ACTIVE
            ),
            intensity=value,
            cycle_ms=self._cycle_ms,
        )
        return self._state

    def pause(self) -> AmbientEffectState:
        """Pause the current effect without losing its configuration."""
        if self._state.active:
            self._state = AmbientEffectState(
                effect=self._state.effect,
                phase=AmbientPhase.PAUSED,
                intensity=self._state.intensity,
                cycle_ms=self._state.cycle_ms,
            )
        return self._state

    def resume(self) -> AmbientEffectState:
        """Resume a paused effect."""
        if self._state.phase == AmbientPhase.PAUSED:
            self._state = AmbientEffectState(
                effect=self._state.effect,
                phase=AmbientPhase.ACTIVE,
                intensity=self._state.intensity,
                cycle_ms=self._state.cycle_ms,
            )
        return self._state

    def stop(self) -> AmbientEffectState:
        """Stop the current effect."""
        self._state = AmbientEffectState(
            cycle_ms=self._cycle_ms,
        )
        return self._state

    @staticmethod
    def wave(
        progress: float,
        *,
        minimum: float = 0.0,
        maximum: float = 1.0,
    ) -> float:
        """Return a deterministic triangular ambient-wave value."""
        if not 0.0 <= progress <= 1.0:
            raise ValueError("progress must be between 0.0 and 1.0")
        if minimum > maximum:
            raise ValueError("minimum must not exceed maximum")

        phase = progress * 2.0
        normalized = (
            phase
            if phase <= 1.0
            else 2.0 - phase
        )
        return minimum + (maximum - minimum) * normalized


__all__ = [
    "AmbientEffect",
    "AmbientEffectController",
    "AmbientEffectState",
    "AmbientPhase",
]
