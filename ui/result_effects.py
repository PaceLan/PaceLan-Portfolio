"""Presentation-layer result, error, and warning effects for M22.5."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ui.animation import AnimationKind, AnimationSpec


class ResultVisualState(str, Enum):
    EXECUTING = "executing"
    COMPLETED = "completed"
    WARNING = "warning"
    FAILED = "failed"
    RECOVERY = "recovery"
    ENDED = "ended"


@dataclass(frozen=True)
class ResultEffect:
    source: ResultVisualState
    target: ResultVisualState
    animation: AnimationSpec
    semantic: str
    terminal: bool = False

    def __post_init__(self) -> None:
        if self.source == self.target:
            raise ValueError("result effect source and target must differ")


class ResultEffectMapper:
    """Maps result workflow changes to presentation effects."""

    _EFFECTS = {
        (
            ResultVisualState.EXECUTING,
            ResultVisualState.COMPLETED,
        ): ResultEffect(
            ResultVisualState.EXECUTING,
            ResultVisualState.COMPLETED,
            AnimationSpec(AnimationKind.FADE, 220, 1),
            "positive",
            True,
        ),
        (
            ResultVisualState.EXECUTING,
            ResultVisualState.WARNING,
        ): ResultEffect(
            ResultVisualState.EXECUTING,
            ResultVisualState.WARNING,
            AnimationSpec(AnimationKind.PULSE, 260, 2),
            "caution",
        ),
        (
            ResultVisualState.EXECUTING,
            ResultVisualState.FAILED,
        ): ResultEffect(
            ResultVisualState.EXECUTING,
            ResultVisualState.FAILED,
            AnimationSpec(AnimationKind.FADE, 220, 1),
            "negative",
        ),
        (
            ResultVisualState.WARNING,
            ResultVisualState.EXECUTING,
        ): ResultEffect(
            ResultVisualState.WARNING,
            ResultVisualState.EXECUTING,
            AnimationSpec(AnimationKind.PULSE, 200, 2),
            "active",
        ),
        (
            ResultVisualState.FAILED,
            ResultVisualState.RECOVERY,
        ): ResultEffect(
            ResultVisualState.FAILED,
            ResultVisualState.RECOVERY,
            AnimationSpec(AnimationKind.SLIDE, 180, 1),
            "informative",
        ),
        (
            ResultVisualState.FAILED,
            ResultVisualState.ENDED,
        ): ResultEffect(
            ResultVisualState.FAILED,
            ResultVisualState.ENDED,
            AnimationSpec(AnimationKind.FADE, 160, 1),
            "negative",
            True,
        ),
        (
            ResultVisualState.RECOVERY,
            ResultVisualState.EXECUTING,
        ): ResultEffect(
            ResultVisualState.RECOVERY,
            ResultVisualState.EXECUTING,
            AnimationSpec(AnimationKind.PULSE, 200, 2),
            "active",
        ),
        (
            ResultVisualState.RECOVERY,
            ResultVisualState.ENDED,
        ): ResultEffect(
            ResultVisualState.RECOVERY,
            ResultVisualState.ENDED,
            AnimationSpec(AnimationKind.FADE, 160, 1),
            "informative",
            True,
        ),
    }

    @classmethod
    def effect(
        cls,
        source: ResultVisualState,
        target: ResultVisualState,
    ) -> ResultEffect | None:
        return cls._EFFECTS.get((source, target))

    @classmethod
    def has_effect(
        cls,
        source: ResultVisualState,
        target: ResultVisualState,
    ) -> bool:
        return (source, target) in cls._EFFECTS

    @classmethod
    def effects(cls) -> tuple[ResultEffect, ...]:
        return tuple(cls._EFFECTS.values())


__all__ = [
    "ResultVisualState",
    "ResultEffect",
    "ResultEffectMapper",
]