"""Ambient visual effects and the M26 global ambient field."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math


class AmbientEffect(str, Enum):
    NONE = "none"
    BREATHING = "breathing"
    ACTIVITY = "activity"
    FOCUS = "focus"


class AmbientPhase(str, Enum):
    IDLE = "idle"
    ACTIVE = "active"
    PAUSED = "paused"


@dataclass(frozen=True)
class AmbientEffectState:
    effect: AmbientEffect = AmbientEffect.NONE
    phase: AmbientPhase = AmbientPhase.IDLE
    intensity: float = 0.0
    cycle_ms: int = 3200

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

    def __init__(self, *, default_intensity: float = 0.35, cycle_ms: int = 3200) -> None:
        if not 0.0 <= default_intensity <= 1.0:
            raise ValueError("default_intensity must be between 0.0 and 1.0")
        if cycle_ms <= 0:
            raise ValueError("cycle_ms must be positive")
        self._default_intensity = default_intensity
        self._cycle_ms = cycle_ms
        self._state = AmbientEffectState(cycle_ms=cycle_ms)

    @property
    def state(self) -> AmbientEffectState:
        return self._state

    def start(self, effect: AmbientEffect, *, intensity: float | None = None) -> AmbientEffectState:
        if not isinstance(effect, AmbientEffect):
            raise TypeError("effect must be an AmbientEffect")
        value = self._default_intensity if intensity is None else intensity
        self._state = AmbientEffectState(
            effect=effect,
            phase=AmbientPhase.IDLE if effect == AmbientEffect.NONE else AmbientPhase.ACTIVE,
            intensity=value,
            cycle_ms=self._cycle_ms,
        )
        return self._state

    def pause(self) -> AmbientEffectState:
        if self._state.active:
            self._state = AmbientEffectState(
                effect=self._state.effect,
                phase=AmbientPhase.PAUSED,
                intensity=self._state.intensity,
                cycle_ms=self._state.cycle_ms,
            )
        return self._state

    def resume(self) -> AmbientEffectState:
        if self._state.phase == AmbientPhase.PAUSED:
            self._state = AmbientEffectState(
                effect=self._state.effect,
                phase=AmbientPhase.ACTIVE,
                intensity=self._state.intensity,
                cycle_ms=self._state.cycle_ms,
            )
        return self._state

    def stop(self) -> AmbientEffectState:
        self._state = AmbientEffectState(cycle_ms=self._cycle_ms)
        return self._state

    @staticmethod
    def wave(progress: float, *, minimum: float = 0.0, maximum: float = 1.0) -> float:
        if not 0.0 <= progress <= 1.0:
            raise ValueError("progress must be between 0.0 and 1.0")
        if minimum > maximum:
            raise ValueError("minimum must not exceed maximum")
        phase = progress * math.tau
        normalized = (math.sin(phase - math.pi / 2.0) + 1.0) / 2.0
        return minimum + (maximum - minimum) * normalized

    def intensity_at(self, progress: float) -> float:
        if not self._state.active:
            return 0.0
        return self.wave(
            progress,
            minimum=self._state.intensity * 0.45,
            maximum=self._state.intensity,
        )


@dataclass(frozen=True)
class AmbientLayer:
    """One large, soft light field inside the global ambient scene."""

    name: str
    color: str
    x: float
    y: float
    radius: float
    opacity: float
    drift: float = 0.0
    cycle_ms: int = 18000

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("name must not be empty")
        if not 0.0 <= self.x <= 1.0 or not 0.0 <= self.y <= 1.0:
            raise ValueError("layer position must be normalized")
        if self.radius <= 0.0:
            raise ValueError("radius must be positive")
        if not 0.0 <= self.opacity <= 1.0:
            raise ValueError("opacity must be between 0.0 and 1.0")
        if self.cycle_ms <= 0:
            raise ValueError("cycle_ms must be positive")


@dataclass(frozen=True)
class AmbientFieldState:
    """Immutable render snapshot for the M26 global ambient field."""

    enabled: bool
    intensity: float
    layers: tuple[AmbientLayer, ...]
    phase: float = 0.0

    def __post_init__(self) -> None:
        if not 0.0 <= self.intensity <= 1.0:
            raise ValueError("intensity must be between 0.0 and 1.0")
        if not 0.0 <= self.phase <= 1.0:
            raise ValueError("phase must be between 0.0 and 1.0")


class AmbientFieldController:
    """Global multi-layer ambient field for the M26 main experience."""

    DEFAULT_LAYERS = (
        AmbientLayer("blue", "#5B8DEF", 0.18, 0.18, 0.42, 0.16, 0.045, 22000),
        AmbientLayer("violet", "#8B7CF6", 0.78, 0.28, 0.48, 0.13, 0.035, 26000),
        AmbientLayer("cyan", "#42C7D8", 0.52, 0.82, 0.44, 0.10, 0.030, 30000),
    )

    def __init__(
        self,
        *,
        intensity: float = 1.0,
        layers: tuple[AmbientLayer, ...] | None = None,
    ) -> None:
        if not 0.0 <= intensity <= 1.0:
            raise ValueError("intensity must be between 0.0 and 1.0")
        self._layers = layers or self.DEFAULT_LAYERS
        self._state = AmbientFieldState(
            enabled=False,
            intensity=intensity,
            layers=self._layers,
        )

    @property
    def state(self) -> AmbientFieldState:
        return self._state

    def start(self) -> AmbientFieldState:
        self._state = AmbientFieldState(
            enabled=True,
            intensity=self._state.intensity,
            layers=self._layers,
            phase=self._state.phase,
        )
        return self._state

    def stop(self) -> AmbientFieldState:
        self._state = AmbientFieldState(
            enabled=False,
            intensity=self._state.intensity,
            layers=self._layers,
            phase=self._state.phase,
        )
        return self._state

    def set_intensity(self, intensity: float) -> AmbientFieldState:
        if not 0.0 <= intensity <= 1.0:
            raise ValueError("intensity must be between 0.0 and 1.0")
        self._state = AmbientFieldState(
            enabled=self._state.enabled,
            intensity=intensity,
            layers=self._layers,
            phase=self._state.phase,
        )
        return self._state

    def snapshot(self, phase: float) -> AmbientFieldState:
        if not 0.0 <= phase <= 1.0:
            raise ValueError("phase must be between 0.0 and 1.0")
        return AmbientFieldState(
            enabled=self._state.enabled,
            intensity=self._state.intensity,
            layers=self._layers,
            phase=phase,
        )

    @staticmethod
    def layer_opacity(layer: AmbientLayer, phase: float, intensity: float) -> float:
        if not 0.0 <= phase <= 1.0:
            raise ValueError("phase must be between 0.0 and 1.0")
        pulse = AmbientEffectController.wave(
            (phase * (18000.0 / layer.cycle_ms) + layer.drift) % 1.0,
            minimum=0.72,
            maximum=1.0,
        )
        return layer.opacity * intensity * pulse


__all__ = [
    "AmbientEffect",
    "AmbientEffectController",
    "AmbientEffectState",
    "AmbientFieldController",
    "AmbientFieldState",
    "AmbientLayer",
    "AmbientPhase",
]
