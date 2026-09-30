"""Presentation-layer workspace micro-interaction effects for M22.6."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from ui.animation import AnimationKind, AnimationSpec


class WorkspaceInteraction(str, Enum):
    SELECT = "select"
    DESELECT = "deselect"
    EXPAND = "expand"
    COLLAPSE = "collapse"
    ACTIVATE = "activate"
    DEACTIVATE = "deactivate"
    FOCUS = "focus"
    BLUR = "blur"
    ENTER_EMPTY = "enter_empty"
    EXIT_EMPTY = "exit_empty"


@dataclass(frozen=True)
class WorkspaceInteractionEffect:
    interaction: WorkspaceInteraction
    animation: AnimationSpec
    semantic: str

    def __post_init__(self) -> None:
        if not self.semantic:
            raise ValueError("semantic must not be empty")


class WorkspaceInteractionMapper:
    """Maps workspace state changes to deterministic visual effects."""

    _EFFECTS = {
        WorkspaceInteraction.SELECT: WorkspaceInteractionEffect(
            WorkspaceInteraction.SELECT,
            AnimationSpec(AnimationKind.FADE, 140, 1),
            "active",
        ),
        WorkspaceInteraction.DESELECT: WorkspaceInteractionEffect(
            WorkspaceInteraction.DESELECT,
            AnimationSpec(AnimationKind.FADE, 120, 1),
            "neutral",
        ),
        WorkspaceInteraction.EXPAND: WorkspaceInteractionEffect(
            WorkspaceInteraction.EXPAND,
            AnimationSpec(AnimationKind.SLIDE, 160, 1),
            "active",
        ),
        WorkspaceInteraction.COLLAPSE: WorkspaceInteractionEffect(
            WorkspaceInteraction.COLLAPSE,
            AnimationSpec(AnimationKind.SLIDE, 140, 1),
            "neutral",
        ),
        WorkspaceInteraction.ACTIVATE: WorkspaceInteractionEffect(
            WorkspaceInteraction.ACTIVATE,
            AnimationSpec(AnimationKind.FADE, 140, 1),
            "active",
        ),
        WorkspaceInteraction.DEACTIVATE: WorkspaceInteractionEffect(
            WorkspaceInteraction.DEACTIVATE,
            AnimationSpec(AnimationKind.FADE, 120, 1),
            "neutral",
        ),
        WorkspaceInteraction.FOCUS: WorkspaceInteractionEffect(
            WorkspaceInteraction.FOCUS,
            AnimationSpec(AnimationKind.FADE, 100, 1),
            "informative",
        ),
        WorkspaceInteraction.BLUR: WorkspaceInteractionEffect(
            WorkspaceInteraction.BLUR,
            AnimationSpec(AnimationKind.FADE, 100, 1),
            "neutral",
        ),
        WorkspaceInteraction.ENTER_EMPTY: WorkspaceInteractionEffect(
            WorkspaceInteraction.ENTER_EMPTY,
            AnimationSpec(AnimationKind.FADE, 180, 1),
            "informative",
        ),
        WorkspaceInteraction.EXIT_EMPTY: WorkspaceInteractionEffect(
            WorkspaceInteraction.EXIT_EMPTY,
            AnimationSpec(AnimationKind.FADE, 180, 1),
            "active",
        ),
    }

    @classmethod
    def effect(
        cls,
        interaction: WorkspaceInteraction,
    ) -> WorkspaceInteractionEffect | None:
        return cls._EFFECTS.get(interaction)

    @classmethod
    def has_effect(cls, interaction: WorkspaceInteraction) -> bool:
        return interaction in cls._EFFECTS

    @classmethod
    def effects(cls) -> tuple[WorkspaceInteractionEffect, ...]:
        return tuple(cls._EFFECTS.values())


__all__ = [
    "WorkspaceInteraction",
    "WorkspaceInteractionEffect",
    "WorkspaceInteractionMapper",
]
