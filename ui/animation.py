"""Presentation-layer animation architecture."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class AnimationKind(str, Enum):
    NONE = "none"
    FADE = "fade"
    PULSE = "pulse"
    SLIDE = "slide"


@dataclass(frozen=True)
class AnimationSpec:
    kind: AnimationKind = AnimationKind.NONE
    duration_ms: int = 0
    steps: int = 1

    def __post_init__(self) -> None:
        if self.duration_ms < 0:
            raise ValueError("duration_ms must be non-negative")
        if self.steps < 1:
            raise ValueError("steps must be positive")


@dataclass(frozen=True)
class AnimationRequest:
    source: str
    target: str
    spec: AnimationSpec

    def __post_init__(self) -> None:
        if not self.source:
            raise ValueError("source must not be empty")
        if not self.target:
            raise ValueError("target must not be empty")


class AnimationController:
    """Deterministic presentation-layer animation coordinator."""

    def __init__(self) -> None:
        self._active: AnimationRequest | None = None

    @property
    def active(self) -> AnimationRequest | None:
        return self._active

    @property
    def is_running(self) -> bool:
        return self._active is not None

    def start(self, request: AnimationRequest) -> AnimationRequest:
        self._active = request
        return request

    def stop(self) -> AnimationRequest | None:
        previous = self._active
        self._active = None
        return previous

    def reset(self) -> None:
        self._active = None
